# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260808_issue127_opencode_vertical_slice_v2",
  "round_id": "round_20260808_issue127_opencode_vertical_slice_v2",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260808_issue127_opencode_vertical_slice_v1",
  "follows_last_round_id": "round_20260808_issue127_opencode_vertical_slice_v1",
  "previous_audit_outcome": "ISSUE127_V1_OWNER_AUDIT_REPAIR_REQUIRED_REAL_WORKTREE_BOUNDED_PROMPT_WINDOWS_LAUNCH_STATE_TIMING",
  "workstream_id": "issue127-opencode-vertical-slice-v2",
  "source_issue": 127,
  "parent_issue": 90,
  "prerequisite_issue": 131,
  "related_research_issue": 126,
  "required_branch": "owner/issue127-opencode-vertical-slice-v1",
  "starting_head": "9d305996b9cefbd5170498e9e9db6577b3a341a5",
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
      "command_id": "test.opencode_executor_focused",
      "command": "python -m pytest tests/platform_v1/test_opencode_executor.py -q",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
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
      "validation_note": "Any failure must be listed by exact test node ID. Only failures whose assertions bind current decision_packet.md to project_state/mainline_merge_intents/active.json or final R2 landing authority may be classified as KNOWN_LANDING_GOVERNANCE_BLOCKER. Do not modify those tests or merge-intent files in this R3 product round. Any other failure is a product blocker and must be repaired."
    },
    {
      "command_id": "acceptance.opencode_task_plane",
      "command": "python -m reverse_agent.platform_v1.opencode_task_plane_acceptance --repo-dir F:/reverse-agent --workspace-root F:/reverse-agent-workspaces/issue127-opencode-v2 --model sensetime/sensenova-6.7-flash-lite",
      "phase": "acceptance",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["model_execution", "network_access", "worktree_creation", "tool_execution", "external_workspace_mutation", "deterministic_validation"],
      "network_access": true,
      "required_evidence_source": "local_command_evidence",
      "validation_note": "Must create a real linked Git worktree from repo_dir using git worktree semantics, not git init. Must prove worktree HEAD/base ancestry and that the Agent can read an existing reverse-agent file inside the worktree before creating the bounded acceptance output. Use the pre-existing non-OpenAI SenseTime/SenseNova route only."
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
    "reverse_agent/model_access/contracts.py",
    "reverse_agent/model_access/store.py",
    "frontend/src/lib/task-client.ts",
    "frontend/src/hooks/use-tasks.ts",
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

Issue #127 v2 is a fail-forward repair round for the accepted v1 runtime direction. The v1 local acceptance proved that a separate OpenCode child process can be dispatched through Task API -> ExecutorRouter -> OpenCodeExecutor and can return normalized evidence. Owner exact-head review found that the implementation is not yet a truthful isolated-repository execution boundary.

The following v1 evidence remains accepted:

```text
OpenCode CLI 1.18.15 resolves on the host
sensetime/sensenova-6.7-flash-lite executes successfully
Task API create/execute/readback/events path works
SQLite persistence works
changed-file / validation / executor evidence plumbing works
Codex calls = 0
OpenHands calls = 0
```

The following v1 findings MUST be repaired before a Draft PR is created:

1. REAL WORKTREE: `OpenCodeExecutor._prepare_git_worktree()` currently uses `git init` in an empty directory. v2 must create a real linked worktree from the configured repository/base using `git worktree add` (or an existing repository utility that is demonstrably equivalent). The Agent must be able to read the target repository contents inside that isolated worktree. It must never operate in the source checkout.
2. BOUNDED PROMPT: v1 uses `_PROMPT_TEMPLATE = "{task}"`. v2 must wrap the user task in a fixed authority envelope that explicitly restricts filesystem scope to the worktree and forbids commit, push, PR, merge, release/deploy, credential access, provider reconfiguration, and work outside the requested task.
3. WINDOWS LAUNCH SAFETY: user-controlled task text must not be interpolated unsafely into a Windows `.cmd` command line. Prefer a native executable when available; otherwise keep user-controlled prompt content out of shell syntax (for example via a bounded prompt file/stdin mechanism supported by the installed CLI) and add metacharacter/injection regression tests. Do not use `shell=True`.
4. STATE TIMING: TaskService must not persist `VALIDATING` before the real executor has even run. Preserve truthful phase ordering. External executor failures should leave an evidence-consistent RUNNING -> BLOCKED/FAILED path; successful execution should enter validation/review states in a truthful order.
5. ACCEPTANCE TRUTH: the real acceptance must prove the workspace is a linked worktree of `F:/reverse-agent`, not merely an unrelated Git repository outside that path. It must verify worktree HEAD/base ancestry and read at least one existing reverse-agent file from the worktree before making the bounded acceptance mutation.
6. GOVERNANCE TEST CLASSIFICATION: the current full Platform V1 suite may fail while this R3 implementation Decision is active because legacy landing tests dynamically require the current Decision to match `mainline_merge_intents/active.json` and an R2 `active_pr` landing authority. List every failing node ID. Do not modify those governance tests or merge intents in v2. Any failure not strictly attributable to that landing-authority mismatch is a product blocker and must be fixed before push.

No frontend, Model Access, Draft-PR publication, one-click launcher, or multi-Agent work is authorized in this repair round.

## Acceptance

v2 is accepted only if all are true:

1. v2 Decision commit precedes v2 gate generation and all repair changes.
2. `transition-lint` passes and preflight is `PRE_EXECUTION_AUTHORIZED` with `blocking_reasons=[]`.
3. OpenCode workspace is created by real repository worktree semantics from the configured `repo_dir` and an approved base ref/SHA; an empty `git init` workspace is forbidden for the opencode executor.
4. Worktree path is outside the source checkout and is present in `git -C <repo_dir> worktree list --porcelain` (or equivalent definitive evidence).
5. Worktree `HEAD` is bound to the requested base/ref and the source checkout HEAD/status remains unchanged.
6. Bounded prompt includes fixed authority constraints and the user task separately; tests verify task text with `&`, `|`, `>`, `<`, `%`, `!`, quotes and newlines cannot become host shell syntax.
7. OpenCode process launching remains `shell=False`; Windows `.cmd` handling uses a tested safe strategy that does not expose user task text to shell interpretation.
8. TaskService no longer transitions to `VALIDATING` before actual executor execution; state/event ordering is evidence-consistent.
9. Focused OpenCode tests pass with 0 failures, including new real-worktree, prompt-boundary, Windows metacharacter, state-ordering, timeout/nonzero/malformed-output, secret-redaction and changed-file tests.
10. Real HTTP acceptance uses a linked reverse-agent worktree, reads an existing repository file, performs one bounded worktree-only mutation, independently validates it, and proves source checkout unchanged.
11. Full `tests/platform_v1` run is recorded. Every failure, if any, is listed by node ID and proven to be only a known landing-governance mismatch. Product/runtime tests must have zero failures.
12. `git diff --check` passes and final changed paths remain Decision-authorized.
13. No `frontend/**`, `reverse_agent/model_access/**`, `.github/**`, docs, dependency files, credentials/configuration, or `project_state/mainline_merge_intents/**` changes.
14. Codex runtime calls = 0; OpenHands runtime calls = 0.
15. Normal push only. No PR / Ready / merge / main push by the local Agent.

Success terminal:

```text
ISSUE127_V2_OPENCODE_BACKEND_REPAIR_READY_FOR_OWNER_AUDIT
```

## Owner follow-up

After v2 exact-head acceptance, Owner may create the Draft PR. CI is expected to expose the known current-Decision-versus-active-landing-intent mismatch until an explicit R2 final landing authority round binds the PR/head/Decision/command-plan. That landing round must not be simulated by weakening Platform V1 tests during this R3 product repair.
