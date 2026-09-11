# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260911_issue771_functional_validation_r2_v1",
  "round_id": "round_20260911_issue771_functional_validation_r2_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": [
    "reverse-agent-iteration@v2"
  ]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "decision_scope": "F03_FIXED_FUNCTIONAL_CHECKS_AND_EXACT_ARTIFACT_CORE",
  "source_issue": 771,
  "parent_issue": 653,
  "repository": "dddd2024/Nerelan",
  "source_issue_body_sha256": "d675d2c30f17ae3d83e0aea3f1bfc6ab034d9948a439848ceceaf87110edf27a",
  "approved_by": "dddd2024 via explicitly delegated Codex owner action",
  "approval_basis": "User expressly authorized project completion, all tools, owner privileges, self-audit and merge in this task. Agent approval is disclosed and is not independent human review.",
  "risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "18a871839a1019251f9997ad0f5a74b8a4230787",
  "activation_base_sha": "18a871839a1019251f9997ad0f5a74b8a4230787",
  "starting_head": "18a871839a1019251f9997ad0f5a74b8a4230787",
  "required_branch": "codex/f03-functional-verification-r2",
  "fresh_worktree_creation_required": true,
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
  "product_change_commit_limit": 8,
  "generated_governance_commit_limit": 4,
  "normal_push_attempt_limit": 12,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 1,
  "merge_attempt_limit": 1,
  "dependency_install_limit": 0,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "credential_access_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": true,
  "pull_request_comment_allowed": true,
  "merge_allowed": true,
  "mark_ready_allowed": true,
  "allowed_merge_method": "merge",
  "workflow_rerun_allowed": false,
  "runner_dispatch_allowed": false,
  "direct_push_to_main_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "dependency_install_allowed": false,
  "live_provider_access_allowed": false,
  "credential_access_allowed": false,
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "no_legacy_intent_mode": "READ_ONLY_LANDING_CANDIDATE_VALIDATION",
  "landing_authority_scope_note": "Read-only landing candidate mode is not itself mutation authority. The separately explicit bounded landing command in this Decision grants only the exact branch PR Ready/merge after the required exact-head evidence and live reobservation, under the user delegation.",
  "semantic_implementation_contract": {
    "issue_body_sha256": "d675d2c30f17ae3d83e0aea3f1bfc6ab034d9948a439848ceceaf87110edf27a",
    "specification": "F03 executable functional validation core. Parent #653; project acceptance #659.\n\nThis R2 Work Item fixes the missing server-side executable oracle, frozen check contract and exact tested artifact identity. It is not execution authority by itself: a fresh bounded APPROVED Decision and its generated Command Plan must pass transition-preflight before source implementation. The user delegated owner actions and self-audit/merge to this Codex task; any agent approval or audit is disclosed as agent activity, not independent human review.\n\nLocked integration base: main@18a871839a1019251f9997ad0f5a74b8a4230787. Fresh branch: codex/f03-functional-verification-r2. Preserve all previous worktrees and original root changes.\n\nImplementation contract:\n\n1. Reuse existing Goal plan/revision/approval and TaskStore. Add optional structured functional checks to each planned task. The host owns a closed catalog: python_pytest and npm_test; callers may select a catalog id and a confined relative working directory, never executable paths, shell strings, arbitrary arguments or environment overrides. Render selected checks in the persisted plan so current Goal approval covers them. Material edits invalidate the plan via the existing revision mechanism.\n2. Freeze the approved per-task checks, catalog version/digest, Goal/revision/artifact digest and repository into existing TaskStore evidence during atomic Goal launch. This must be transactionally bound to Task creation and idempotent retries. No second store or new governance Gate. No DB migration is required; reuse existing task evidence and Goal tasks JSON.\n3. The server runs selected checks on the executor's actual prepared worktree after implementation/review, through fixed structured argv and installed Python/npm runtimes. npm must never install dependencies; set CI/offline behavior, disable automatic audits/funding and interactive input. Confine working directories to the prepared repository, reject traversal and symlink escapes, bound runtime/output and terminate timed-out child processes. Do not inherit browser-provided command authority. Missing runtime/profile/contract is explicit failure or unverified state, never functional success.\n4. Reuse existing Git private-index workspace snapshot support for exact base/head/tree identities before and after checks; preserve the real index. Retain diff hygiene as supplementary evidence. Require actual implementation changes for implementation tasks, matching before/after artifact identity, all required checks with successful exit codes, and matching frozen command contract. A mutated artifact, wrong base, missing or stale evidence, no tests, syntax error, failed assertion or no implementation cannot be called functionally verified.\n5. Integrate this oracle into ordinary and durable single/sequential execution, including resume/retry/reconciliation boundaries. Do not let an executor's claimed success or a prior diff-check overwrite functional failure. Persist bounded per-check command identity, resolved argv identity, exit/timing/output digest and exact tested artifact identifiers through existing TaskStore evidence/fenced writes. Preserve leases and checkpoint ownership. Fixture execution remains clearly fixture; legacy Tasks without approved functional checks retain truthful PATCH_HYGIENE/UNVERIFIED behavior.\n6. Expose safe structured functional evidence through existing Task and Run read models. Functional verification, review readiness, Draft publication and merge stay distinct; a SUCCESS exit code alone is insufficient. Do not read arbitrary logs or expose raw environment/secrets. Existing workflow-name required_checks contracts must not be reinterpreted as local commands.\n7. Verify with real temporary Git repositories, SQLite, installed pytest and a bounded fake/local npm test fixture. Exercise valid implementation, syntax error, failed test, zero tests/no implementation, malformed/unknown/unapproved checks, output/time bounds, directory confinement, mutation during validation, changed contract/base, durable retry/resume and duplicate launch. At least one real Goal plan/approval/launch -> server execution -> persisted Task/Run readback must demonstrate both rejection and successful functional proof without models/providers or network.\n\nExact source/test allowlist:\n\n```text\nreverse_agent/platform_v1/functional_validation.py\nreverse_agent/platform_v1/goal_service.py\nreverse_agent/platform_v1/run_store.py\nreverse_agent/platform_v1/task_runtime.py\nreverse_agent/platform_v1/task_execution.py\nreverse_agent/platform_v1/durable_execution.py\nreverse_agent/platform_v1/task_service.py\nreverse_agent/platform_v1/run_read_model.py\ntests/platform_v1/test_functional_validation.py\ntests/platform_v1/test_goal_functional_checks.py\ntests/platform_v1/test_functional_execution.py\ntests/platform_v1/test_task_execution.py\ntests/platform_v1/test_durable_execution.py\ntests/platform_v1/test_run_read_model.py\ntests/platform_v1/test_task_service.py\ndocs/functional-validation.md\n```\n\nThe Decision activation may change only project_state/decision_packet.md before implementation. Existing generated gate paths may be written only by their generator commands and published only when the bounded Decision explicitly permits them. No authority/validator implementation, workflow, dependencies, lockfiles, frontend, model/credential code or reverse/binary product work is included.\n\nRequired local checks:\n\n```text\npython -B -m pytest tests/platform_v1/test_functional_validation.py tests/platform_v1/test_goal_functional_checks.py tests/platform_v1/test_functional_execution.py tests/platform_v1/test_goal_service.py tests/platform_v1/test_goal_configuration.py tests/platform_v1/test_goal_plan_revision.py tests/platform_v1/test_task_execution.py tests/platform_v1/test_durable_execution.py tests/platform_v1/test_durable_execution_v5.py tests/platform_v1/test_run_read_model.py tests/platform_v1/test_task_service.py -q -p no:cacheprovider\ngit diff --check\n```\n\nRun startup-snapshot, transition-command-plan, transition-lint, transition-preflight pre and worktree-publication-readiness at their required boundaries. Natural exact-head CI/Decision Preflight/State Gate/Model Access must pass; compare actual diagnostic failed node IDs with the locked baseline, preserving known #687 debt without hiding new failures. No CI rerun/dispatch, dependency installation, provider calls, credentials, local browser execution, screenshots, destructive cleanup or history rewrite.\n\nDraft publication is limited to the exact named branch and repository. No product/source/test mutation before the committed immutable Decision and PRE_EXECUTION_AUTHORIZED. Final Ready/merge requires separately recorded exact-head audit, natural checks and immediate live base/head/clean-merge verification under explicit bounded landing authority. No direct main push, auto-merge, force push, tag/release/deploy.\n\nF03 completion boundary: this is the executable backend prerequisite. The full parent remains open until selecting/reviewing these checks and their proof is integrated into the real user interface and end-to-end product acceptance is demonstrated. F02 cross-Task artifact handoff, #643 publication, real provider/runtime/Edge acceptance and diagnostics remain separate. Do not redefine overall success around backend tests alone.\n"
  },
  "bootstrap_exception_files": [
    "project_state/decision_packet.md"
  ],
  "bootstrap_exception_commands": [],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/platform_v1/functional_validation.py",
    "reverse_agent/platform_v1/goal_service.py",
    "reverse_agent/platform_v1/run_store.py",
    "reverse_agent/platform_v1/task_runtime.py",
    "reverse_agent/platform_v1/task_execution.py",
    "reverse_agent/platform_v1/durable_execution.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/run_read_model.py",
    "tests/platform_v1/test_functional_validation.py",
    "tests/platform_v1/test_goal_functional_checks.py",
    "tests/platform_v1/test_functional_execution.py",
    "tests/platform_v1/test_task_execution.py",
    "tests/platform_v1/test_durable_execution.py",
    "tests/platform_v1/test_run_read_model.py",
    "tests/platform_v1/test_task_service.py",
    "docs/functional-validation.md"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/platform_v1/functional_validation.py",
    "reverse_agent/platform_v1/goal_service.py",
    "reverse_agent/platform_v1/run_store.py",
    "reverse_agent/platform_v1/task_runtime.py",
    "reverse_agent/platform_v1/task_execution.py",
    "reverse_agent/platform_v1/durable_execution.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/run_read_model.py",
    "tests/platform_v1/test_functional_validation.py",
    "tests/platform_v1/test_goal_functional_checks.py",
    "tests/platform_v1/test_functional_execution.py",
    "tests/platform_v1/test_task_execution.py",
    "tests/platform_v1/test_durable_execution.py",
    "tests/platform_v1/test_run_read_model.py",
    "tests/platform_v1/test_task_service.py",
    "docs/functional-validation.md"
  ],
  "reference_paths": [
    "reverse_agent/executor_neutral/core.py"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md",
    ".github/**",
    ".codex-skills/**",
    "frontend/**",
    "reverse_agent/control_plane/**",
    "reverse_agent/project_gate.py",
    "reverse_agent/decision_preflight.py",
    "reverse_agent/mainline_landing.py",
    "pyproject.toml",
    "requirements*.txt",
    "**/secrets/**",
    "**/.env",
    "project_state/mainline_merge_intents/**"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "force_push",
    "rebase",
    "tag_or_release",
    "runner_dispatch",
    "model_api_invocation",
    "external_reverse_tool_invocation",
    "unknown_binary_execution",
    "destructive"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "bmad_installation_allowed": false,
    "network_access_default_allowed": false,
    "direct_push_to_main_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "merge_allowed": true,
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [],
    "ci_network_exceptions": [],
    "trusted_worker_network_exceptions": [],
    "github_control_plane_network_exceptions": [
      "After blocking checks pass, push only codex/f03-functional-verification-r2 and create/update one Draft PR in dddd2024/Nerelan against main at 18a871839a1019251f9997ad0f5a74b8a4230787; publish disclosed audit/evidence and Issue 771/653/659 progress comments; no other branch or repository publication.",
      "Only after disclosed exact-head self-audit, required natural checks, unchanged approved Decision and immediate remote main 18a871839a1019251f9997ad0f5a74b8a4230787, exact reviewed head and CLEAN/MERGEABLE observation, mark the bound PR ready; require natural final State/Landing checks, reobserve immediately and perform one ordinary merge with expected-head protection. Verify merged commit and main and exact parents. This action is explicitly delegated by the user; never claim independent human review."
    ],
    "user_local_network_exceptions": []
  },
  "path_risk_floor": [
    {
      "pattern": "project_state/**",
      "minimum_risk": "R2"
    }
  ],
  "allowed_commands": [
    {
      "command_id": "issue771.bootstrap",
      "command": "Verify the locked base and fresh branch; commit only this immutable Decision as the first activation commit; run startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre and worktree-publication-readiness; require PRE_EXECUTION_AUTHORIZED and PUBLICATION_READY before product edits.",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "trusted_worker",
      "operations": [
        "code_read",
        "local_static_check",
        "command_plan_generation"
      ],
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
      "command_id": "issue771.implement",
      "command": "Implement only the exact F03 functional validation contract and sixteen source/test/documentation paths bound to Issue 771; preserve TaskStore, Goal approval and lease ownership; no workflow, dependency, provider, credential, browser or reverse-tool operation.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "trusted_worker",
      "operations": [
        "source_edit",
        "commit",
        "local_static_check"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/platform_v1/functional_validation.py",
        "reverse_agent/platform_v1/goal_service.py",
        "reverse_agent/platform_v1/run_store.py",
        "reverse_agent/platform_v1/task_runtime.py",
        "reverse_agent/platform_v1/task_execution.py",
        "reverse_agent/platform_v1/durable_execution.py",
        "reverse_agent/platform_v1/task_service.py",
        "reverse_agent/platform_v1/run_read_model.py",
        "tests/platform_v1/test_functional_validation.py",
        "tests/platform_v1/test_goal_functional_checks.py",
        "tests/platform_v1/test_functional_execution.py",
        "tests/platform_v1/test_task_execution.py",
        "tests/platform_v1/test_durable_execution.py",
        "tests/platform_v1/test_run_read_model.py",
        "tests/platform_v1/test_task_service.py",
        "docs/functional-validation.md"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "issue771.validate",
      "command": "python -B -m pytest tests/platform_v1/test_functional_validation.py tests/platform_v1/test_goal_functional_checks.py tests/platform_v1/test_functional_execution.py tests/platform_v1/test_goal_service.py tests/platform_v1/test_goal_configuration.py tests/platform_v1/test_goal_plan_revision.py tests/platform_v1/test_task_execution.py tests/platform_v1/test_durable_execution.py tests/platform_v1/test_durable_execution_v5.py tests/platform_v1/test_run_read_model.py tests/platform_v1/test_task_service.py -q -p no:cacheprovider\ngit diff --check\nRun transition lint, preflight and publication readiness; test only approved deterministic fixtures and local runtimes without model/provider/network access.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "trusted_worker",
      "operations": [
        "unit_test",
        "integration_test",
        "diff_validation",
        "local_static_check"
      ],
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
      "command_id": "issue771.publish",
      "command": "After blocking checks pass, push only codex/f03-functional-verification-r2 and create/update one Draft PR in dddd2024/Nerelan against main at 18a871839a1019251f9997ad0f5a74b8a4230787; publish disclosed audit/evidence and Issue 771/653/659 progress comments; no other branch or repository publication.",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "github_control_plane",
      "operations": [
        "push",
        "draft_pr",
        "pull_request_comment",
        "issue_comment",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue771.audit",
      "command": "Observe natural exact-head CI, Decision Preflight, State Gate and Model Access; compare actual diagnostic failed node IDs with the locked base and perform a separate disclosed self-audit. No rerun or dispatch.",
      "phase": "final_evidence",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "remote_observation",
      "operations": [
        "read_only_audit",
        "code_read"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue771.landing",
      "command": "Only after disclosed exact-head self-audit, required natural checks, unchanged approved Decision and immediate remote main 18a871839a1019251f9997ad0f5a74b8a4230787, exact reviewed head and CLEAN/MERGEABLE observation, mark the bound PR ready; require natural final State/Landing checks, reobserve immediately and perform one ordinary merge with expected-head protection. Verify merged commit and main and exact parents. This action is explicitly delegated by the user; never claim independent human review.",
      "phase": "final_acceptance",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "github_control_plane",
      "operations": [
        "mark_ready",
        "merge",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ]
}
```
