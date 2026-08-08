# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260808_issue127_opencode_vertical_slice_v1",
  "round_id": "round_20260808_issue127_opencode_vertical_slice_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260807_pr129_provider_free_task_plane_landing_v5",
  "follows_last_round_id": "round_20260807_pr129_provider_free_task_plane_landing_v5",
  "previous_audit_outcome": "ISSUE131_V2_ACCEPTED_OPENCODE_RUN_REAL_EXECUTOR_ESTABLISHED",
  "workstream_id": "issue127-opencode-vertical-slice-v1",
  "source_issue": 127,
  "parent_issue": 90,
  "prerequisite_issue": 131,
  "related_research_issue": 126,
  "required_branch": "owner/issue127-opencode-vertical-slice-v1",
  "starting_head": "e4e23028c6c78c4ab9a8e032677e71370ace7627",
  "activation_base_sha": "e4e23028c6c78c4ab9a8e032677e71370ace7627",
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
  "repair_attempt_limit": 2,
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
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "git status --short",
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
      "command_id": "gate.startup_snapshot",
      "command": "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["gate_execution"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": ["project_state/gates/startup_snapshot.json"]
    },
    {
      "command_id": "gate.transition_command_plan",
      "command": "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["gate_execution"],
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
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["gate_execution"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "gate.transition_preflight",
      "command": "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["gate_execution"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "project_state/gates/transition_preflight_result.json",
        "project_state/gates/bootstrap_state.json"
      ]
    },
    {
      "command_id": "test.opencode_executor_unit",
      "command": "python -m pytest tests/platform_v1 -q",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "acceptance.opencode_task_plane",
      "command": "python -m reverse_agent.platform_v1.opencode_task_plane_acceptance --repo-dir F:/reverse-agent --workspace-root F:/reverse-agent-workspaces/issue127-opencode-v1 --model sensetime/sensenova-6.7-flash-lite",
      "phase": "acceptance",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["model_execution", "network_access", "worktree_creation", "tool_execution", "external_workspace_mutation", "deterministic_validation"],
      "network_access": true,
      "required_evidence_source": "local_command_evidence",
      "validation_note": "Must invoke the installed OpenCode CLI as a separate child process using the pre-existing non-OpenAI SenseTime/SenseNova route. No Codex/OpenHands invocation, provider reconfiguration, or credential-value access. Acceptance worktree must be outside F:/reverse-agent tracked source."
    },
    {
      "command_id": "validation.diff_check",
      "command": "git diff --check e4e23028c6c78c4ab9a8e032677e71370ace7627..HEAD",
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
      "command": "git diff --name-only e4e23028c6c78c4ab9a8e032677e71370ace7627..HEAD",
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
      "command": "git push origin owner/issue127-opencode-vertical-slice-v1",
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
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/platform_v1/opencode_task_plane_acceptance.py",
    "reverse_agent/platform_v1/task_runtime.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/run_store.py",
    "tests/platform_v1/**"
  ],
  "reference_paths": [
    "AGENTS.md",
    "README.md",
    "pyproject.toml",
    "reverse_agent/project_gate.py",
    "reverse_agent/platform_v1/task_runtime.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/run_store.py",
    "reverse_agent/coordinator_adapters.py",
    "reverse_agent/model_access/contracts.py",
    "reverse_agent/model_access/store.py",
    "frontend/src/lib/task-client.ts",
    "frontend/src/hooks/use-tasks.ts",
    "tests/platform_v1/**",
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
    "frontend/**",
    "reverse_agent/model_access/**",
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
    "merge"
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
      "git fetch origin owner/issue127-opencode-vertical-slice-v1",
      "git push origin owner/issue127-opencode-vertical-slice-v1"
    ],
    "ci_network_exceptions": []
  },
  "authorized_risk_tier": "R3",
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/**",
    "reverse_agent/platform_v1/**",
    "tests/platform_v1/**"
  ],
  "path_risk_floor": [
    {"pattern": "project_state/decision_packet.md", "minimum_risk": "R2"},
    {"pattern": "project_state/gates/**", "minimum_risk": "R2"},
    {"pattern": "reverse_agent/platform_v1/**", "minimum_risk": "R2"}
  ]
}
```

## Goal

Issue #127 implementation v1 starts from the provider-free task plane already landed by PR #129 and the real OpenCode executor proof accepted from Issue #131 v2.

This round is deliberately narrower than the full historical Issue #127 body. The following pieces already exist on `main` and MUST be reused, not rewritten:

```text
Frontend task submission/readback chain
loopback-only Task API
SQLite TaskStore / idempotency
ExecutorRouter abstraction
activity / changed-file / evidence normalization
provider-free deterministic fixture executor
```

The only product goal in this round is:

```text
POST /api/tasks (executor_kind=opencode)
→ POST /api/tasks/{id}/execute
→ existing ExecutorRouter
→ real OpenCodeExecutor child process
→ isolated Git worktree outside the source tree
→ read / shell / edit
→ deterministic git diff validation
→ normalized changed-files / events / evidence
→ GET task readback
```

No frontend rewrite, no Model Access rewrite, no Draft-PR publication, no one-click launcher, and no multi-Agent work in this round.

## Implementation constraints

1. Add a thin `OpenCodeExecutor`; do not embed a second scheduler/orchestrator.
2. Invoke the already-proven `opencode run` child-process surface. Do not use OpenCode Desktop IPC/ACP in this round.
3. Use a non-secret explicit runtime model setting, preferably constructor injection with a bounded environment fallback such as `REVERSE_AGENT_OPENCODE_MODEL`. The v1 local acceptance value is `sensetime/sensenova-6.7-flash-lite`.
4. Do not read or migrate provider credentials. OpenCode owns its pre-existing provider session/configuration.
5. Run only in an isolated Git worktree outside `F:/reverse-agent`; do not let the model mutate the source checkout directly.
6. Reuse existing Git/worktree utilities where compatible. Do not wholesale port old branches or PR #114.
7. The Agent prompt must explicitly prohibit commit, push, PR, merge, release, or files outside the worktree.
8. Capture and sanitize bounded JSON/event output from OpenCode. Never persist auth values, full environment dumps, or unbounded raw logs.
9. Keep existing deterministic fixture behavior and tests working. Backward compatibility is required.
10. Generalize runtime state only as much as needed for a real executor. If introducing `RUNNING` / `READY_FOR_REVIEW`, retain compatibility with existing `RUNNING_FIXTURE` / `READY_FOR_REVIEW_FIXTURE` persisted fixture tasks.
11. Task API may accept `executor_kind=opencode`; unsupported kinds remain fail-closed.
12. Validation truth is deterministic command evidence, not Agent prose.

## Acceptance

The round is accepted only if all are true:

1. Decision commit precedes generated gates and product changes.
2. `transition-lint` passes and preflight is `PRE_EXECUTION_AUTHORIZED` with `blocking_reasons=[]`.
3. Unit tests do not require a live provider; subprocess/CLI behavior is injectable and testable with fakes.
4. Existing provider-free fixture tests continue to pass.
5. A real local acceptance invokes a separate OpenCode CLI child process with the pre-existing non-OpenAI SenseNova route.
6. Acceptance runs against a disposable Git repository/worktree outside the reverse-agent source tree.
7. HTTP chain succeeds: create → execute → task readback → events readback.
8. Runtime evidence proves: workspace prepared, executor started, at least one real file mutation, deterministic validation exit 0, changed files recorded, executor/model evidence recorded, and terminal state maps to `READY_FOR_HUMAN`.
9. OpenCode exit/nonzero/timeout/malformed output are normalized without leaking credentials; external/provider blockers are distinguishable from product validation failures.
10. `git diff --check` passes.
11. Final diff contains only Decision-authorized paths.
12. No `frontend/**`, `reverse_agent/model_access/**`, workflows, dependencies, docs, merge intents, or credential/config files are modified.
13. Codex runtime calls = 0. OpenHands runtime calls = 0.
14. Branch is normal-pushed only. Local Agent creates no PR and performs no merge/Ready/main push.

Success terminal:

```text
ISSUE127_V1_OPENCODE_BACKEND_VERTICAL_SLICE_READY_FOR_OWNER_AUDIT
```

## Follow-up after this round

Only after Owner accepts this backend vertical slice should Issue #127 proceed to the next bounded round:

```text
frontend executor/model cutover
→ real frontend-created task
→ Draft PR publication through trusted GitHub adapter
→ one-click dev-up
→ first reverse-agent-on-reverse-agent dogfood
```

This separation prevents frontend/Draft-PR work from obscuring whether the real executor boundary itself is reliable.
