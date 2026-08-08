# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260808_issue127_opencode_vertical_slice_v3",
  "round_id": "round_20260808_issue127_opencode_vertical_slice_v3",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260808_issue127_opencode_vertical_slice_v2",
  "follows_last_round_id": "round_20260808_issue127_opencode_vertical_slice_v2",
  "previous_audit_outcome": "ISSUE127_V2_SUPERSEDED_PREEXECUTION_BY_EXTENDED_OWNER_EVIDENCE_SAFETY_AUDIT",
  "workstream_id": "issue127-opencode-vertical-slice-v3",
  "source_issue": 127,
  "parent_issue": 90,
  "prerequisite_issue": 131,
  "related_research_issue": 126,
  "required_branch": "owner/issue127-opencode-vertical-slice-v1",
  "starting_head": "e8106de9378a657d9e0ca435991003b55c4e1e51",
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
      "validation_note": "List every failing test node ID. Only tests whose failure is caused by the active R3 Decision not matching final R2 mainline_merge_intents authority may be KNOWN_LANDING_GOVERNANCE_BLOCKER. Do not modify those tests or merge intents in this round. Any other failure is a product blocker."
    },
    {
      "command_id": "acceptance.opencode_task_plane",
      "command": "python -m reverse_agent.platform_v1.opencode_task_plane_acceptance --repo-dir F:/reverse-agent --workspace-root F:/reverse-agent-workspaces/issue127-opencode-v3 --model sensetime/sensenova-6.7-flash-lite",
      "phase": "acceptance",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["model_execution", "network_access", "worktree_creation", "tool_execution", "external_workspace_mutation", "deterministic_validation"],
      "network_access": true,
      "required_evidence_source": "local_command_evidence",
      "validation_note": "Must create a real linked Git worktree from repo_dir; prove HEAD/base binding, worktree-list membership, source checkout unchanged, actual read of an existing reverse-agent file, real tool/action evidence from OpenCode JSON, one bounded mutation, accurate changed-file statistics, and independent validation."
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

Issue #127 v3 is the single repair round to make the OpenCode backend slice truthful enough for a Draft PR. v1 proved the runtime route but Owner review found the acceptance could pass without executing against the target repository. v2 was created as an initial repair authority but was superseded before gate generation or local repair so the evidence-safety findings below could be handled in the same implementation round.

Accepted runtime direction:

```text
Task API -> ExecutorRouter -> OpenCode child process -> deterministic validation -> TaskStore readback
OpenCode CLI 1.18.15
sensetime/sensenova-6.7-flash-lite
Codex calls = 0
OpenHands calls = 0
```

Required repairs:

1. REAL LINKED WORKTREE. Replace the empty `git init` workspace with a worktree linked to configured `repo_dir`, using a resolved approved base commit/ref. Prefer `git -C <repo_dir> worktree add --detach <path> <base>` or an equivalent existing repository utility. Fail closed on invalid repo/base or pre-existing conflicting workspace. Do not mutate the source checkout.
2. BOUNDED AUTHORITY PROMPT. Wrap task text in a fixed executor-owned authority envelope restricting tools/filesystem to the worktree and forbidding commit, push, PR, merge, release/deploy, credential access, provider configuration changes, and unrelated work.
3. WINDOWS COMMAND BOUNDARY. Browser/task-controlled text and model identifiers must not become shell syntax when the installed OpenCode entrypoint is `.cmd`. Validate model identifiers. Keep `shell=False`. Prefer a safe native executable when available; otherwise keep user-controlled prompt text out of the `.cmd` command string by using a tested executor-owned prompt-file/stdin/attachment mechanism supported by the installed CLI. Add metacharacter regression tests (`& | > < % ! ^ quotes newlines`).
4. TRUTHFUL STATE/EVENT ORDER. Do not persist `VALIDATING` before the child process has run. Avoid duplicate synthetic OpenCode lifecycle events where the executor already supplies the same event. Final status/evidence must correspond to actual runtime order.
5. REAL STRUCTURED EXECUTOR EVIDENCE. Parsed OpenCode JSON action/tool events must not be discarded on success. Persist a bounded, normalized, recursively redacted summary sufficient to prove real executor/tool activity without storing arbitrary unbounded provider payloads.
6. RECURSIVE SECRET REDACTION. Redact sensitive keys/values at nested dict/list depths before any OpenCode event/log persistence. Tests must cover nested Authorization/token/api-key/cookie/credential structures and bearer-like values. Preserve safe structural metadata where possible instead of stringifying entire nested objects.
7. ACCURATE CHANGED-FILE EVIDENCE. Untracked file `additions` must represent diff/line semantics rather than file byte size. Binary/unreadable files must be handled conservatively and deterministically.
8. ACCEPTANCE TRUTH. Acceptance must prove the workspace is listed by the target repository's worktree metadata, its HEAD is bound to the selected base, it can read an existing reverse-agent file from that worktree, the model performs a bounded worktree-only mutation, and the source checkout HEAD/status is unchanged.
9. NO FABRICATED COUNTERS. Acceptance failure output must not claim `model_calls=0` after an OpenCode attempt may already have occurred. Track explicit attempted/completed child-process counts or omit unknown counters. Codex/OpenHands zero may only be asserted from code paths that do not invoke them.
10. GOVERNANCE TEST CLASSIFICATION. Record every full `tests/platform_v1` failure by exact node ID. Only final-landing tests that dynamically bind the active R3 Decision to `mainline_merge_intents/active.json`, `active_pr`, or R2 landing authority may remain as `KNOWN_LANDING_GOVERNANCE_BLOCKER`. Do not modify those tests/merge intents in this R3 round. Any other failing test blocks publication.

No frontend, Model Access, Draft-PR publication, one-click launcher, dependency installation, or multi-Agent work is authorized.

## Acceptance

v3 is accepted only if all are true:

1. This v3 Decision commit precedes v3 gate generation and repair changes.
2. transition-lint PASS; transition-preflight `PRE_EXECUTION_AUTHORIZED`; `blocking_reasons=[]`.
3. Focused OpenCode tests pass with zero failures and cover every repair above.
4. Real acceptance creates a linked worktree of `F:/reverse-agent`, proves worktree registration and exact base HEAD, and proves source checkout unchanged.
5. Acceptance proves at least one read of an existing repository file, one real OpenCode tool/shell action, one bounded mutation, one structured executor action evidence record, accurate changed-file data, and independent `git diff --check` validation exit 0.
6. OpenCode process exit 0 and task terminal state maps to `READY_FOR_HUMAN` only after deterministic validation.
7. Failure-path tests cover CLI unavailable, model identifier rejection/unavailable route, timeout, malformed output, nonzero exit, validation failure, nested-secret redaction, worktree-preparation failure, and Windows metacharacter safety.
8. Full Platform V1 diagnostic is recorded; non-governance product/runtime failures = 0. Known landing-governance failures are enumerated, not hidden.
9. `git diff --check` passes and all changes remain inside authorized paths.
10. No frontend/model-access/workflow/dependency/docs/merge-intent/credential/config changes.
11. Codex runtime calls = 0; OpenHands runtime calls = 0.
12. Normal push only; local Agent performs no PR/Ready/merge/main push.

Success terminal:

```text
ISSUE127_V3_OPENCODE_BACKEND_REPAIR_READY_FOR_OWNER_AUDIT
```

## Owner follow-up

After v3 exact-head acceptance, Owner will create a Draft PR. Remote CI may remain red only for the known current-R3-Decision versus final landing-intent assertions. Owner will then create a separate R2 PR landing authority bound to the Draft PR exact head, regenerate landing gates/intent, and require full remote CI success before Ready/merge.
