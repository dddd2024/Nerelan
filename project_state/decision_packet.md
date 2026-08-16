# Decision Packet

```json decision_meta
{"schema_version":1,"decision_id":"decision_20260816_issue209_heartbeat_evidence_recovery_r2_v1","round_id":"round_20260816_issue209_heartbeat_evidence_recovery_r2_v1","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2"]}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260816_issue204_durable_process_smoke1_r2_v4",
  "follows_last_round_id": "round_20260816_issue204_durable_process_smoke1_r2_v4",
  "previous_audit_outcome": "ISSUE204_EXISTING_EVIDENCE_MISSING_REQUIRED_SECOND_HEARTBEAT_SAMPLE",
  "workstream_id": "issue209-heartbeat-evidence-recovery-r2-v1",
  "source_issue": 209,
  "parent_issue": 204,
  "parent_roadmap_issue": 148,
  "related_flaky_test_issue": 207,
  "required_branch": "owner/issue209-heartbeat-evidence-recovery-r2-v1",
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
      "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue209-heartbeat-evidence-recovery-r2-v1",
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
    "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue209-heartbeat-evidence-recovery-r2-v1",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/repository-modernization-v2-planning",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/issue209-heartbeat-evidence-recovery-r2-v1",
    "powershell -NoProfile -Command \"$b=(git -C F:/reverse-agent-planning-smoke branch --list owner/issue209-heartbeat-evidence-recovery-r2-v1);if($b){'ISSUE209_V1_LOCAL_BRANCH_ALREADY_EXISTS';exit 25};if(Test-Path -LiteralPath 'F:/reverse-agent-issue209-heartbeat-evidence-r2-v1'){'ISSUE209_V1_AUTH_WORKTREE_ALREADY_EXISTS';exit 24};if(Test-Path -LiteralPath 'F:/reverse-agent-issue209-heartbeat-source-v1'){'ISSUE209_V1_SOURCE_WORKTREE_ALREADY_EXISTS';exit 23};if(Test-Path -LiteralPath 'F:/reverse-agent-issue209-heartbeat-evidence-v1'){'ISSUE209_V1_SMOKE_ROOT_ALREADY_EXISTS';exit 22};'ISSUE209_V1_BOOTSTRAP_TARGETS_ABSENT'\"",
    "git -C F:/reverse-agent-planning-smoke worktree add --track -b owner/issue209-heartbeat-evidence-recovery-r2-v1 F:/reverse-agent-issue209-heartbeat-evidence-r2-v1 origin/owner/issue209-heartbeat-evidence-recovery-r2-v1",
    "Set-Location F:/reverse-agent-issue209-heartbeat-evidence-r2-v1",
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
      "command_id": "issue209v1.dependencies_install",
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
      "command_id": "issue209v1.dependencies_identity",
      "command": "python -c \"import importlib.metadata as m; assert m.version('langgraph')=='1.0.10'; assert m.version('langgraph-checkpoint-sqlite')=='3.1.0'; print('ISSUE209_V1_DEPENDENCIES_OK')\"",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue209v1.source_create",
      "command": "git worktree add --detach F:/reverse-agent-issue209-heartbeat-source-v1 deed415c7dff3101b18aac6a3ea0cc01fc5eba3c",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["worktree_creation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue209v1.source_identity",
      "command": "python -c \"import subprocess;root=r'F:/reverse-agent-issue209-heartbeat-source-v1';h=subprocess.check_output(['git','-C',root,'rev-parse','HEAD'],text=True).strip();assert h=='deed415c7dff3101b18aac6a3ea0cc01fc5eba3c',h;s=subprocess.check_output(['git','-C',root,'status','--porcelain'],text=True);assert not s,s;print('ISSUE209_V1_SOURCE_IDENTITY_OK',h)\"",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue209v1.smoke_root_create",
      "command": "powershell -NoProfile -Command \"New-Item -ItemType Directory -Path 'F:/reverse-agent-issue209-heartbeat-evidence-v1' -ErrorAction Stop | Out-Null; Write-Output 'ISSUE209_V1_SMOKE_ROOT_CREATED'\"",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["external_evidence_directory_creation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue209v1.smoke_driver",
      "command": "python F:/reverse-agent-issue209-heartbeat-evidence-v1/smoke_driver.py --source F:/reverse-agent-issue209-heartbeat-source-v1 --root F:/reverse-agent-issue209-heartbeat-evidence-v1/runtime --planning deed415c7dff3101b18aac6a3ea0cc01fc5eba3c",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "subprocess_crash_recovery_smoke", "os_process_kill", "linked_worktree_smoke"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue209v1.source_unchanged",
      "command": "python -c \"import subprocess;root=r'F:/reverse-agent-issue209-heartbeat-source-v1';h=subprocess.check_output(['git','-C',root,'rev-parse','HEAD'],text=True).strip();assert h=='deed415c7dff3101b18aac6a3ea0cc01fc5eba3c',h;s=subprocess.check_output(['git','-C',root,'status','--porcelain'],text=True);assert not s,s;print('ISSUE209_V1_SOURCE_UNCHANGED')\"",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue209v1.authority_diff_check",
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
      "command_id": "issue209v1.final_status",
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

Recover the missing heartbeat evidence for #204 without changing repository product/test code. Run two fresh provider-free OS-kill/recovery cases from canonical planning and persist the two required pre-kill heartbeat samples per case.

# Explicit external harness write authorization

After and only after bootstrap succeeds, transition gates return `PRE_EXECUTION_AUTHORIZED` with `blocking_reasons=[]`, and required command `issue209v1.smoke_root_create` succeeds, the local Agent is explicitly authorized to create exactly this disposable external harness file using its editor/file-write capability:

`F:/reverse-agent-issue209-heartbeat-evidence-v1/smoke_driver.py`

The file is outside repository mutation scope. It must never be added to Git, committed, pushed, copied into the repository, or generated through an unlisted shell command. Do not create additional executable/script files. Runtime JSON/JSONL/SQLite/marker/log artifacts may be created by the authorized harness only beneath `F:/reverse-agent-issue209-heartbeat-evidence-v1/runtime`. Run the completed harness only through required command `issue209v1.smoke_driver` exactly as written above.

# Mandatory heartbeat evidence delta

For each independent case (`POST_PLANNER` and `POST_CODER`), after the target checkpoint marker exists and while the crash child remains alive, the parent must read the persisted TaskStore twice and append **two distinct structured records** to `monitor.heartbeat_samples`.

Each record must contain at least:

- `observed_at_ms` — parent's observation wall-clock time;
- `heartbeat_at_ms` — persisted crash-epoch heartbeat from TaskStore;
- `lease_expiry_ms`;
- `owner`;
- `epoch`;
- `child_alive`.

Acceptance requires all of:

1. exactly two or more persisted pre-kill samples exist in `monitor.heartbeat_samples`;
2. choose two ordered samples `s1`, `s2` with `s2.observed_at_ms > s1.observed_at_ms`;
3. `s2.heartbeat_at_ms > s1.heartbeat_at_ms`;
4. both heartbeat values are nonzero;
5. both samples use the same nonempty crash owner;
6. both samples use the same crash epoch;
7. `child_alive == true` for both;
8. both `observed_at_ms` values and both persisted heartbeat values are strictly earlier than the parent kill timestamp;
9. only after these assertions pass may the parent invoke `Popen.kill()`;
10. final `summary.json` must preserve the full sample arrays and the human-readable report must print the exact sample values for both cases.

The sampling loop must be bounded. Waiting long enough for the configured production heartbeat interval to advance is permitted. Do not edit TaskStore timestamps to manufacture evidence.

# Preserved v4 semantics

This recovery does not weaken any v4 acceptance invariant. Both cases must still prove:

1. real parent-driven `Popen.kill()` / Windows process termination after accepted target checkpoint; `_CrashSimulated` or graceful exit is not acceptance evidence;
2. immediately after kill, old owner/epoch/expiry remain persisted and no graceful lease release occurred;
3. no lease/heartbeat timestamp mutation; wait for actual persisted expiry before recovery;
4. fresh Python recovery OS process;
5. `reconcile_expired_runs()` -> Task `INTERRUPTED`, classification `orphan_stale_lease`;
6. one heartbeat using old owner+old epoch raises `TaskStoreError`;
7. recovery epoch is strictly greater than crash epoch;
8. execution worktree is a real linked Git worktree created from exact source/planning SHA; no `git init`, no fake repository, no commits by fake roles;
9. recovery reuses the persisted worktree and checkpoint DB;
10. POST_PLANNER crash roles exactly Planner=1/Coder=0/Reviewer=0, recovery roles Planner=0/Coder=1/Reviewer=1;
11. POST_CODER crash roles exactly Planner=1/Coder=1/Reviewer=0, recovery roles Planner=0/Coder=0/Reviewer=1;
12. POST_CODER `coder_product_diff_digest` is nonempty before kill and matched by reconstructed worktree product snapshot on recovery;
13. exactly one durable run per task;
14. checkpoint history exactly `PRE_PLANNER,POST_PLANNER,POST_CODER,POST_REVIEWER,POST_VALIDATION`, each once;
15. final Task `READY_FOR_REVIEW`, accepted checkpoint `POST_VALIDATION`, validation exit 0;
16. same task/execution/run/worktree/base/checkpoint-DB identities before and after recovery;
17. detached source remains exact planning and clean;
18. zero OpenCode/Codex/OpenHands/model/provider/credential-relay calls and no external network use during smoke execution;
19. #207 remains isolated and is not grounds for scope expansion.

# Fake role contract

Planner creates only `.reverse-agent-handoff/plan.md`. Coder requires the plan and makes one deterministic uncommitted product change only inside the linked execution worktree. Reviewer creates only `.reverse-agent-handoff/review.md`. External role logs are appended only after successful fake-role completion. No role may mutate the detached source.

# v4 preservation

Do not delete, edit, reuse, reset, attach, or otherwise mutate the existing v4 authority worktree or `F:/reverse-agent-durable-process-smoke1-v4`. It remains immutable historical evidence.

# Fail closed

Any bootstrap, gate, identity, heartbeat-ordering/aliveness, kill, lease, recovery, checkpoint, role, digest, worktree, source-cleanliness, or zero-invocation invariant failure must stop as:

`ISSUE204_HEARTBEAT_EVIDENCE_RECOVERY_BOUNDED_FAILURE`

Preserve external evidence and do not patch repository product/test code in this round.

Success prints exactly:

`ISSUE204_HEARTBEAT_EVIDENCE_RECOVERY_ACCEPTED`

After success, report the two exact heartbeat samples for each case, kill timestamps, crash/recovery PIDs and all preserved v4 invariants. Owner will then close #209 and #204 and move to Long-running Unattended Dogfood 1.
