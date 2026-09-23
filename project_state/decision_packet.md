# Decision Packet — Issue #120 resume write-gate

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260923_issue120_resume_write_gate_r2_v1",
  "round_id": "round_20260923_issue120_resume_write_gate_r2_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "decision_scope": "ISSUE120_RESUME_WRITE_GATE",
  "source_issue": 120,
  "parent_issue": 137,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 via explicit current request to resolve Issue #120 and persist the fix to GitHub",
  "approval_basis": "The repository owner explicitly requested that the current Issue #120 resume-safety problem be solved and fixed on GitHub. This bounded R2 Decision is delegated Agent authoring, not independent human review. It authorizes only a Draft implementation of a server-side Resume write-gate using already-landed authority/autonomy/budget/durable-execution primitives; it grants no Ready, Merge, direct-main push, workflow rerun/dispatch, provider call, credential access or release.",
  "risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "3b9eb3806ca59e119d2f8db36537b7efe593c729",
  "activation_base_sha": "3b9eb3806ca59e119d2f8db36537b7efe593c729",
  "starting_head": "3b9eb3806ca59e119d2f8db36537b7efe593c729",
  "required_branch": "owner/issue120-resume-write-gate-r2-v1-20260923",
  "fresh_worktree_creation_required": false,
  "history_reuse_allowed": false,
  "decision_commit_must_precede_implementation": true,
  "decision_commit_must_precede_execution": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_immutability_check_required_in": [
    "transition_preflight",
    "transition_reconcile",
    "worktree_publication_readiness"
  ],
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 3,
  "generated_governance_commit_limit": 1,
  "normal_push_attempt_limit": 5,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "workflow_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "credential_access_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": true,
  "pull_request_comment_allowed": true,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "workflow_rerun_allowed": false,
  "workflow_dispatch_allowed": false,
  "runner_dispatch_allowed": false,
  "direct_push_to_main_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "dependency_install_allowed": false,
  "live_provider_access_allowed": false,
  "credential_access_allowed": false,
  "local_browser_execution_allowed": false,
  "model_api_invocation_allowed": false,
  "external_reverse_tool_invocation_allowed": false,
  "unknown_binary_execution_allowed": false,
  "destructive_operations_allowed": false,
  "provider_free_acceptance_required": true,
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "semantic_implementation_contract": {
    "specification": "Close the concrete Issue #120 write-gate gap at the public POST /api/tasks/{task_id}/resume boundary. Reuse the existing TaskStore/PlatformControlStore, AutonomyService resume_task authorization, owner-activated window, atomic claim/budget reservation, and DurableExecutionService authority/planning/repository/worktree validation. Manual Resume must not reach durable executor/tool re-entry unless the task is INTERRUPTED, is linked to its current RUNNING Goal and owner window, resume_task is currently authorized for the task repository, and current token/cost admission can be reserved. Preserve existing durable authority SHA/planning SHA and HEAD/worktree fail-closed checks; do not create a second RunStore, quota ledger, policy engine or generic resume state machine. Provider-official quota truth remains distinct from Nerelan local budget truth: do not fabricate provider remaining quota when no trustworthy source exists. The server gate is authoritative; a stale advisory UI control may receive HTTP 409 rather than being allowed to bypass the gate.",
    "execution_surface_note": "GitHub-first activation and publication. The user-local Remote Desktop device is not required for this provider-free change. Natural repository workflows and an actual full checkout provide transition/preflight and exact-head test evidence. No live provider/model calls, credentials or dependency installation.",
    "completion_boundary": "Draft implementation only. Exact-head deterministic tests must prove denied/missing owner authority and exhausted token/cost admission cannot call durable Resume, while an admitted interrupted task calls exactly one correct durable resume path and finalizes the claim. Existing durable authority/planning mismatch regressions must remain green. No Ready/Merge or Issue closure in this Decision."
  },
  "bootstrap_exception_files": ["project_state/decision_packet.md"],
  "bootstrap_exception_commands": [],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/platform_v1/task_service.py",
    "tests/platform_v1/test_task_service.py"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/platform_v1/task_service.py",
    "tests/platform_v1/test_task_service.py"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "AGENTS.md",
    "docs/agents/governance-reference.md",
    "reverse_agent/platform_v1/autonomy.py",
    "reverse_agent/platform_v1/control_store.py",
    "reverse_agent/platform_v1/durable_execution.py",
    "reverse_agent/platform_v1/unattended_coordinator.py",
    "reverse_agent/platform_v1/run_read_model.py",
    "reverse_agent/model_access/provider_usage.py",
    "tests/platform_v1/test_durable_execution.py",
    "tests/platform_v1/test_unattended_coordinator.py",
    "tests/platform_v1/test_run_resume_control.py"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md",
    "docs/agents/**",
    ".github/**",
    ".codex-skills/**",
    "reverse_agent/platform_v1/autonomy.py",
    "reverse_agent/platform_v1/control_store.py",
    "reverse_agent/platform_v1/durable_execution.py",
    "reverse_agent/platform_v1/unattended_coordinator.py",
    "reverse_agent/platform_v1/run_read_model.py",
    "reverse_agent/model_access/**",
    "frontend/**",
    "tests/platform_v1/test_durable_execution.py",
    "tests/platform_v1/test_unattended_coordinator.py",
    "tests/platform_v1/test_run_resume_control.py",
    "project_state/rounds/**",
    "project_state/mainline_merge_intents/**",
    "pyproject.toml",
    "requirements*.txt",
    "**/secrets/**",
    "**/.env"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "auto_merge",
    "force_push",
    "rebase",
    "squash",
    "amend",
    "history_rewrite",
    "mark_ready",
    "merge",
    "workflow_rerun",
    "workflow_dispatch",
    "runner_dispatch",
    "model_api_invocation",
    "provider_network_call",
    "credential_access",
    "unknown_binary_execution",
    "external_reverse_tool_invocation",
    "destructive",
    "tag_or_release",
    "dependency_install",
    "local_browser_execution"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "workflow_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "network_access_default_allowed": false,
    "direct_push_to_main_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "merge_allowed": false,
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [],
    "ci_network_exceptions": [],
    "trusted_worker_network_exceptions": [],
    "user_local_network_exceptions": [],
    "github_control_plane_network_exceptions": [
      "Publish only owner/issue120-resume-write-gate-r2-v1-20260923 in dddd2024/Nerelan and one Draft PR against main@3b9eb3806ca59e119d2f8db36537b7efe593c729. Initial publication is Decision-only. Semantic publication requires actual PRE_EXECUTION_AUTHORIZED evidence. Update that Draft and comment on Issue #120 only. Never Ready or Merge."
    ]
  },
  "path_risk_floor": [
    {"pattern": "project_state/**", "minimum_risk": "R2"},
    {"pattern": "reverse_agent/platform_v1/task_service.py", "minimum_risk": "R2"}
  ],
  "allowed_commands": [
    {
      "command_id": "issue120.bootstrap",
      "command": "On the exact fresh branch/base, verify the immutable Decision-only activation and run the repository transition startup snapshot, command-plan generation, transition lint, transition preflight --mode pre, and applicable publication-readiness gate. Natural GitHub workflows may produce the same evidence in their full checkout. Do not fabricate successful gates.",
      "phase": "bootstrap",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "trusted_worker",
      "operations": ["code_read", "local_static_check", "command_plan_generation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": [
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "issue120.implement",
      "command": "Only after actual PRE_EXECUTION_AUTHORIZED evidence, implement the smallest server-side manual Resume write-gate in reverse_agent/platform_v1/task_service.py and provider-free focused regressions in tests/platform_v1/test_task_service.py. Reuse existing AutonomyService authorization, current Goal/window, PlatformControlStore claim/budget reservation, and DurableExecutionService authority checks. No second policy, budget, quota or resume subsystem.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "trusted_worker",
      "operations": ["source_edit", "unit_test", "local_static_check"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/platform_v1/task_service.py",
        "tests/platform_v1/test_task_service.py"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "issue120.validate",
      "command": "On a full exact-head checkout run python -m pytest -q tests/platform_v1/test_task_service.py tests/platform_v1/test_durable_execution.py tests/platform_v1/test_unattended_coordinator.py tests/platform_v1/test_run_resume_control.py and git diff --check. Existing exact-head CI remains mandatory. No provider/model call, skip, dependency change or weakened expectation.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "ci_only",
      "operations": ["unit_test", "local_static_check", "diff_validation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue120.publish",
      "command": "Publish only owner/issue120-resume-write-gate-r2-v1-20260923 and its single Draft PR against exact main@3b9eb3806ca59e119d2f8db36537b7efe593c729. Rebind the Draft exact_head_sha after implementation and post a concise Issue #120 handoff/reply. Never Ready or Merge.",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "github_control_plane",
      "operations": ["push", "draft_pr", "pull_request_comment", "issue_comment", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue120.observe",
      "command": "Fresh-read exact base/head, natural State Gate/Decision Preflight/CI and the scoped diff. Confirm denied authority/budget paths cannot reach durable Resume and existing authority/head checks remain intact. Do not call self-review independent acceptance or treat a Draft as landed.",
      "phase": "final_evidence",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "remote_observation",
      "operations": ["read_only_audit", "code_read"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "issue_completion_close_allowed": []
}
```

## Goal

Close the concrete public Resume admission gap identified in Issue #120 without rebuilding durable execution.

## Build vs reuse decision

```text
REUSE current DurableExecutionService checkpoint/authority/HEAD fail-closed validation
REUSE current AutonomyService owner-window + resume_task capability authorization
REUSE current PlatformControlStore claim and token/cost reservation accounting
SELF-DEVELOP only the thin Task API write-gate and focused regressions
NO new dependency / RunStore / quota ledger / provider collector / policy engine
```

Provider-official quota and rate-limit observations remain the distinct #667 truth domain; this slice does not invent upstream remaining quota when it is unavailable.

## Acceptance

1. public manual Resume requires an INTERRUPTED task linked to a current RUNNING Goal/owner window;
2. current `resume_task` repository/capability authority is rechecked immediately before admission;
3. current token/cost admission is atomically reserved before durable resume dispatch;
4. authority/planning SHA and repository/worktree/HEAD checks remain enforced by the durable resume layer before executor/tool re-entry;
5. missing/expired/stopped/out-of-scope authority returns a bounded conflict and makes zero durable-resume calls;
6. exhausted token/cost budget returns a bounded conflict and makes zero durable-resume calls;
7. an admitted task calls exactly one correct durable resume path and finalizes its claim;
8. provider-free regression suite and exact-head CI pass;
9. no destructive cleanup, provider calls, secrets, dependency changes, second resume state machine or second usage/quota ledger.

## Stop conditions

Changed base, Decision mutation, missing pre-execution authorization, out-of-scope diff, failed mandatory checks, authority mismatch, budget denial, or unavailable required CI proof stops semantic publication. Preserve evidence and fail closed.
