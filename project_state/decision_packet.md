# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260808_issue127_opencode_vertical_slice_v4",
  "round_id": "round_20260808_issue127_opencode_vertical_slice_v4",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260808_issue127_opencode_vertical_slice_v3",
  "follows_last_round_id": "round_20260808_issue127_opencode_vertical_slice_v3",
  "previous_audit_outcome": "ISSUE127_V3_REWORK_REQUIRED_EXACT_HEAD_TRUTHFULNESS",
  "workstream_id": "issue127-opencode-vertical-slice-v4",
  "source_issue": 127,
  "parent_issue": 90,
  "prerequisite_issue": 131,
  "related_research_issue": 126,
  "required_branch": "owner/issue127-opencode-vertical-slice-v1",
  "starting_head": "271e001a570338c259ac739afaafa71e85dc6494",
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
      "command_id": "observation.v3_dirty_executor_diff",
      "command": "git diff -- reverse_agent/platform_v1/opencode_executor.py",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "local_progress_reconciliation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "validation_note": "The v3 acceptance reported this tracked file dirty at HEAD 271e001a. Preserve and inspect the exact diff before any mutation. If it is intended v3/v4 work, incorporate it explicitly under this Decision; if unrelated or unclear, do not discard it and instead perform v4 in a separate safe worktree."
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
      "command_id": "test.v4_focused",
      "command": "python -m pytest tests/platform_v1/test_opencode_executor.py tests/platform_v1/test_task_service.py -q",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "validation_note": "Must include new regressions for authority-envelope transport, shell/metacharacter isolation, real linked-worktree behavior, and TaskService not entering VALIDATING before real executor execution completes."
    },
    {
      "command_id": "test.platform_v1_full_diagnostic",
      "command": "python -m pytest tests/platform_v1 -q",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0, 1],
      "execution_surface": "local",
      "operations": ["run_checks", "landing_governance_failure_classification"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "validation_note": "List every failing node ID. Only failures caused solely by active engineering R3 authority not matching final R2 mainline_merge_intents authority may be KNOWN_LANDING_GOVERNANCE_BLOCKER. Any other failure is a product blocker. Do not weaken tests or mutate merge intents in v4."
    },
    {
      "command_id": "validation.create_clean_exact_head_source",
      "command": "git worktree add --detach F:/reverse-agent-workspaces/issue127-opencode-v4-source HEAD",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["worktree_creation", "external_workspace_mutation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "validation_note": "Run only after the intended v4 implementation and generated gate artifacts are committed. Destination must not pre-exist; do not delete or overwrite an existing path."
    },
    {
      "command_id": "validation.clean_source_status_before",
      "command": "git -C F:/reverse-agent-workspaces/issue127-opencode-v4-source status --short",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "validation_note": "Output must be empty before exact-head tests/acceptance."
    },
    {
      "command_id": "validation.exact_head_focused",
      "command": "powershell -NoProfile -Command \"Set-Location 'F:/reverse-agent-workspaces/issue127-opencode-v4-source'; python -m pytest tests/platform_v1/test_opencode_executor.py tests/platform_v1/test_task_service.py -q\"",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "exact_head_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.exact_head_full_platform",
      "command": "powershell -NoProfile -Command \"Set-Location 'F:/reverse-agent-workspaces/issue127-opencode-v4-source'; python -m pytest tests/platform_v1 -q\"",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0, 1],
      "execution_surface": "local",
      "operations": ["run_checks", "exact_head_validation", "landing_governance_failure_classification"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "acceptance.opencode_task_plane_exact_head",
      "command": "powershell -NoProfile -Command \"Set-Location 'F:/reverse-agent-workspaces/issue127-opencode-v4-source'; python -m reverse_agent.platform_v1.opencode_task_plane_acceptance --repo-dir F:/reverse-agent-workspaces/issue127-opencode-v4-source --workspace-root F:/reverse-agent-workspaces/issue127-opencode-v4-runtime --model sensetime/sensenova-6.7-flash-lite\"",
      "phase": "acceptance",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["model_execution", "network_access", "worktree_creation", "tool_execution", "external_workspace_mutation", "deterministic_validation", "exact_head_validation"],
      "network_access": true,
      "required_evidence_source": "local_command_evidence",
      "validation_note": "Python code and target repo_dir must both come from the clean detached exact-head validation worktree. PASS must prove real linked worktree, read/tool/edit, bounded persisted evidence, accurate line stats, independent validation, truthful call counters, and source validation worktree unchanged."
    },
    {
      "command_id": "validation.clean_source_status_after",
      "command": "git -C F:/reverse-agent-workspaces/issue127-opencode-v4-source status --short",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "exact_head_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "validation_note": "Output must remain empty after real acceptance."
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
    "reverse_agent/platform_v1/task_service.py",
    "tests/platform_v1/test_opencode_executor.py",
    "tests/platform_v1/test_task_service.py"
  ],
  "reference_paths": [
    "AGENTS.md",
    "README.md",
    "pyproject.toml",
    "reverse_agent/project_gate.py",
    "reverse_agent/platform_v1/task_runtime.py",
    "reverse_agent/platform_v1/run_store.py",
    "reverse_agent/model_access/contracts.py",
    "reverse_agent/model_access/store.py",
    "frontend/src/lib/task-client.ts",
    "frontend/src/hooks/use-tasks.ts",
    "tests/platform_v1/test_contracts.py",
    "tests/platform_v1/test_merge_intent.py",
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
    "frontend/**",
    "reverse_agent/model_access/**",
    "reverse_agent/platform_v1/task_runtime.py",
    "reverse_agent/platform_v1/run_store.py",
    "docs/**",
    "project_state/mainline_merge_intents/**",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/schemas/**",
    "project_state/rounds/**",
    "project_state/audits/**",
    "tests/platform_v1/test_contracts.py",
    "tests/platform_v1/test_merge_intent.py"
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
      "git fetch origin owner/issue127-opencode-vertical-slice-v1",
      "git push origin owner/issue127-opencode-vertical-slice-v1"
    ],
    "ci_network_exceptions": []
  },
  "authorized_risk_tier": "R3",
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/**",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/platform_v1/opencode_task_plane_acceptance.py",
    "reverse_agent/platform_v1/task_service.py",
    "tests/platform_v1/test_opencode_executor.py",
    "tests/platform_v1/test_task_service.py"
  ],
  "path_risk_floor": [
    {"pattern": "project_state/decision_packet.md", "minimum_risk": "R2"},
    {"pattern": "project_state/gates/**", "minimum_risk": "R2"},
    {"pattern": "reverse_agent/platform_v1/**", "minimum_risk": "R2"}
  ]
}
```

## Goal

Issue #127 v4 is a minimal fail-forward round after Owner exact-head audit rejected v3 head `271e001a570338c259ac739afaafa71e85dc6494` as not yet Draft-PR-ready.

The OpenCode runtime architecture is still accepted. v4 does not redesign or replace the executor. It closes only exact-head truthfulness and missing regression coverage.

## Owner findings

### V4-F1 — TaskService timeline remains false on pushed v3 head

At `271e001a...`, `task_service.py` still transitions `PREPARING_WORKSPACE -> RUNNING -> VALIDATING` before calling `_run_executor(...)`. A real OpenCode task must remain RUNNING while the child executor performs its execution phase. v4 must move the service-level VALIDATING transition until after real executor execution has completed, and add a regression proving the executor is invoked while task state is RUNNING rather than VALIDATING.

### V4-F2 — v3 runtime acceptance was not exact-head clean

The reported acceptance used HEAD `271e001a...` while `git status --short` simultaneously reported `M reverse_agent/platform_v1/opencode_executor.py` before and after the run. Therefore the runtime evidence proves a dirty working-tree variant, not the exact pushed GitHub tree.

v4 must inspect and preserve that local diff first. Do not discard it. After v4 implementation is committed, create the dedicated detached validation source worktree and run both pytest and real OpenCode acceptance from that clean exact HEAD. The validation worktree must be clean before and after acceptance.

### V4-F3 — required regressions are missing from the pushed test suite

The pushed `tests/platform_v1/test_opencode_executor.py` does not contain the v3-required metacharacter/task-text isolation, authority-envelope, or real linked-worktree regressions, and there is no focused TaskService timeline assertion tied to this repair.

v4 must add deterministic tests for:

```text
authority envelope wraps untrusted task text
metacharacters/newlines/command-looking text never become executable shell syntax
prompt-file transport keeps task text out of the fixed positional shell surface
real repo_dir path creates a registered linked worktree rather than standalone git init
existing worktree destination fails closed rather than recursive deletion
TaskService invokes the real executor while backend state is RUNNING, not VALIDATING
```

## Existing accepted evidence retained

Do not repeat research that is already accepted:

```text
OpenCode CLI 1.18.15 exists
sensetime/sensenova-6.7-flash-lite is configured
real OpenCode read/tool/edit/verify route works
ExecutorRouter can dispatch OpenCode
SQLite evidence/readback works
linked-worktree implementation exists on remote head
bounded ExecutorAction evidence exists
line-based untracked-file statistics exist
Codex/OpenHands calls remain zero for this workstream
```

## Landing-governance boundary

The 12 `test_contracts.py` / `test_merge_intent.py` failures reported in v3 remain a separate expected landing-authority mismatch while `project_state/mainline_merge_intents/active.json` still describes PR #129. v4 MUST NOT modify merge intents or weaken those tests.

They may remain `KNOWN_LANDING_GOVERNANCE_BLOCKER` only if the exact-head v4 full suite shows the same cause and no additional product failure.

## Local-state preservation

The next local executor must resume from the actual local state and preserve every unknown staged, unstaged, and untracked file. In particular:

```text
DO NOT git clean
DO NOT reset --hard
DO NOT rebase
DO NOT force-push
DO NOT amend/squash
DO NOT blanket-stage
DO NOT delete the dirty opencode_executor.py diff without first recording and classifying it
```

If the existing checkout cannot safely become the v4 execution checkout, use a separate safe worktree rather than discarding local work.

## Terminal target

```text
ISSUE127_V4_EXACT_HEAD_BACKEND_SLICE_READY_FOR_OWNER_AUDIT
```

Local executor must normal-push the tested branch and stop. It must not create a PR, mark Ready, mutate merge intents, merge, tag, release, or deploy.
