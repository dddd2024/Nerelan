# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260911_issue776_functional_ui_r2_v1",
  "round_id": "round_20260911_issue776_functional_ui_r2_v1",
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
  "decision_scope": "F03_UI_APPROVED_CHECK_SELECTION_AND_BOUND_PROOF",
  "source_issue": 776,
  "parent_issue": 653,
  "repository": "dddd2024/Nerelan",
  "source_issue_body_sha256": "32a6e4f587f28dc2afad6ccd94db08eca62dd0cdf1053573bfa6ba509e617c24",
  "approved_by": "dddd2024 via explicitly delegated Codex owner action",
  "approval_basis": "User expressly authorized project completion, all tools, owner privileges, self-audit and merge in this task. Agent approval is disclosed and is not independent human review.",
  "risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "139baff28ef86ccbe1c5da008bd4dff7f954f68b",
  "activation_base_sha": "139baff28ef86ccbe1c5da008bd4dff7f954f68b",
  "starting_head": "139baff28ef86ccbe1c5da008bd4dff7f954f68b",
  "required_branch": "codex/f03-functional-check-selection-and-evidence",
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
    "issue_body_sha256": "32a6e4f587f28dc2afad6ccd94db08eca62dd0cdf1053573bfa6ba509e617c24",
    "specification": "F03 user-facing continuation after accepted backend Issue #771 / merged PR #772; parent functional audit #653 and overall acceptance #659 remain open.\n\nThis Issue is a candidate and grants no execution authority. The user explicitly delegated Owner actions, self-audit and merge in the active project goal. Activate a fresh bounded APPROVED R2 Decision before implementation and disclose all approval/audit/publication actions as Codex activity, not independent human review.\n\nLocked integration base: main@139baff28ef86ccbe1c5da008bd4dff7f954f68b. Fresh target branch: codex/f03-functional-check-selection-and-evidence. Backend accepted head4780723f4ac124276765cd8c680c36aefe598341; mainline State Gate34586282449 has verified the actual merge and emitted the bound integration receipt. Re-observe current main before activation; any base movement requires fresh authority, not rebase/history rewrite.\n\nProblem and intended behavior:\n\n- The host now freezes approved validation_checks and executes fixed installed pytest/npm profiles against exact Git artifacts. The existing Goal review editor offers no way to select them, and PlatformGoal.tasks has no typed field. Add a closed profile selector and repository-relative working directory for each planned Task, with add/remove controls up to the host's eight distinct pairs. No free-form command, environment or timeout authority in the browser.\n- Reuse the existing same-Goal plan revision API, explicit review/approval/launch controls and server-rendered plan. Preserve check selections through unrelated edits, reload and retry; adding/removing/changing checks revises the planned Goal and invalidates stale approval attempts. Approved/launched plans retain the existing immutability policy. No auto-approval or auto-launch during editing. The mock plan renderer must represent selected checks while remaining an explicit mock.\n- Task API supplies safe functionalValidation evidence, but task-client/use-task/use-tasks discard it. The client also emits camelCase validation/execution identities while the hooks inspect only snake_case aliases. Carry the relevant identities and safe proof through the complete existing adapter->hook->TaskDetail path.\n- Reuse one small typed proof adapter/view for Task and Run details. Show host-reported verification state, selected profile/directory, exit code and actual passed/failed/skipped counts, plus inspectable exact base/head/tree and evidence digest. Missing/stale/fixture/failed proof must not display functional success merely because exit code is zero. Keep patch hygiene, functional verification, review readiness, Draft publication and delivery visibly distinct. Never create trusted receipts or an authority store in the browser; do not expose raw test output, argv environment or credentials.\n- Keep existing layout/accessibility patterns; controls must work with keyboard and narrow layouts. Prefer conditional evidence detail to unbounded logs. No unrelated visual redesign or snapshot replacement.\n\nExact allowed product paths:\n\n```text\nfrontend/src/types/index.ts\nfrontend/src/lib/platform-client.ts\nfrontend/src/lib/goal-continuation-operation.ts\nfrontend/src/lib/task-client.ts\nfrontend/src/lib/functional-validation.ts\nfrontend/src/hooks/use-task.ts\nfrontend/src/hooks/use-tasks.ts\nfrontend/src/components/goal-review-editor.tsx\nfrontend/src/components/functional-validation.tsx\nfrontend/src/components/task-detail.tsx\nfrontend/src/routes/runs.tsx\nfrontend/tests/goal-review-editor.test.tsx\nfrontend/tests/goal-configuration-client.test.ts\nfrontend/tests/task-status-mapping.test.ts\nfrontend/tests/runs.test.tsx\nfrontend/tests/functional-validation.test.tsx\nfrontend/e2e/functional-validation.spec.ts\ndocs/functional-validation.md\n```\n\nAuthority paths are limited to the immutable Decision and the existing generated gate files explicitly enumerated in the fresh Decision. No backend execution/store/control-plane/gate-validator/workflow/dependency/lockfile/credential/provider change; no database migration, second store or new receipt/gate/schema. Reuse already installed frontend/Python tooling without dependency installation or package changes. Keep unrelated worktrees and generated local observations intact.\n\nRequired validation:\n\n1. All frontend unit/component tests and production frontend build; meaningful new tests cover selection persistence, add/remove/duplicates/invalid directories, stale editing, explicit approval boundaries, adapter/hook identity retention, missing/stale/fixture/failed/verified evidence, and Task/Run rendering. Do not weaken old assertions or suppress failures.\n2. Existing backend regression files tests/platform_v1/test_goal_functional_checks.py, tests/platform_v1/test_functional_execution.py, tests/platform_v1/test_goal_configuration.py and tests/platform_v1/test_goal_plan_revision.py; git diff --check.\n3. Actual changed TypeScript client modules -> isolated loopback Task API -> disk SQLite plan/review/approve/launch and evidence readback, using a real local Git test repository and installed pytest for actual functional outcomes. Only model execution/binding metadata may be explicit local fakes; never describe them as real provider acceptance. Reopen SQLite and verify same Goal/Task/contract/artifact identities. Cover successful and failed checks, missing/fixture proof and selection removal/stale revision handling. Reuse existing service/test seams, not a parallel application API. Retain sanitized probe evidence outside the repository.\n4. Natural exact-head CI, Decision Preflight, State Gate, Model Access and Frontend Playwright when triggered by their existing path filters. The added Playwright flow covers visible plan editing/review with explicit mock limitations; it cannot alone close F03. No workflow rerun/dispatch, assertion weakening, local browser execution or snapshot update under this R2 round. Compare actual full-suite diagnostic failures against the locked base, separately from workflow conclusion.\n5. Separate disclosed exact-head self-audit and a reviewable Draft. Agent Ready/merge requires the bounded Path-B landing sequence and existing false/none authority/attestation protocol; no human-independent review claim. Fresh no-drift, required formal landing context and expected-head ordinary merge protection remain mandatory.\n\nLocal loopback integration is limited to ephemeral test servers and temporary test SQLite/Git workspaces, zero model/provider calls and no credential access. Live provider, actual desktop/Sidecar and Edge/visual product acceptance remain separately bounded final-project work. Parent #653 must remain open until the full user-visible real-flow requirements are proved. No main push, force push, rebase/squash/amend, auto-merge, tag/release/deploy, arbitrary network or destructive cleanup.\n"
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
    "frontend/src/types/index.ts",
    "frontend/src/lib/platform-client.ts",
    "frontend/src/lib/goal-continuation-operation.ts",
    "frontend/src/lib/task-client.ts",
    "frontend/src/lib/functional-validation.ts",
    "frontend/src/hooks/use-task.ts",
    "frontend/src/hooks/use-tasks.ts",
    "frontend/src/components/goal-review-editor.tsx",
    "frontend/src/components/functional-validation.tsx",
    "frontend/src/components/task-detail.tsx",
    "frontend/src/routes/runs.tsx",
    "frontend/tests/goal-review-editor.test.tsx",
    "frontend/tests/goal-configuration-client.test.ts",
    "frontend/tests/task-status-mapping.test.ts",
    "frontend/tests/runs.test.tsx",
    "frontend/tests/functional-validation.test.tsx",
    "frontend/e2e/functional-validation.spec.ts",
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
    "frontend/src/types/index.ts",
    "frontend/src/lib/platform-client.ts",
    "frontend/src/lib/goal-continuation-operation.ts",
    "frontend/src/lib/task-client.ts",
    "frontend/src/lib/functional-validation.ts",
    "frontend/src/hooks/use-task.ts",
    "frontend/src/hooks/use-tasks.ts",
    "frontend/src/components/goal-review-editor.tsx",
    "frontend/src/components/functional-validation.tsx",
    "frontend/src/components/task-detail.tsx",
    "frontend/src/routes/runs.tsx",
    "frontend/tests/goal-review-editor.test.tsx",
    "frontend/tests/goal-configuration-client.test.ts",
    "frontend/tests/task-status-mapping.test.ts",
    "frontend/tests/runs.test.tsx",
    "frontend/tests/functional-validation.test.tsx",
    "frontend/e2e/functional-validation.spec.ts",
    "docs/functional-validation.md"
  ],
  "reference_paths": [
    "reverse_agent/platform_v1/functional_validation.py",
    "reverse_agent/platform_v1/goal_service.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/run_read_model.py"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md",
    ".github/**",
    ".codex-skills/**",
    "reverse_agent/**",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/e2e/snapshots/**",
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
    "destructive",
    "browser_execution",
    "snapshot_update",
    "dependency_install",
    "workflow_dispatch",
    "active_json_rewrite"
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
    "local_network_exceptions": [
      "Run all frontend unit/component tests with the existing npm test script and the existing npm run build production build, without installing dependencies. Run python -B -m pytest tests/platform_v1/test_goal_functional_checks.py tests/platform_v1/test_functional_execution.py tests/platform_v1/test_goal_configuration.py tests/platform_v1/test_goal_plan_revision.py -q -p no:cacheprovider, and git diff --check. Perform the Issue 776 actual changed-TypeScript client to isolated loopback Task API to disk SQLite/Git/installed-pytest integration, with only model execution and binding metadata as explicit local fakes; verify successful/failed/missing/fixture proof and selection/stale-revision handling with reopened SQLite. Reuse installed tooling and existing test/service seams, retain sanitized evidence outside the repository, and close owned test servers after use. No external network, providers, credentials, local browsers or snapshot updates. Run transition lint, preflight and publication readiness; require passing checks before publication."
    ],
    "ci_network_exceptions": [],
    "trusted_worker_network_exceptions": [
      "Run all frontend unit/component tests with the existing npm test script and the existing npm run build production build, without installing dependencies. Run python -B -m pytest tests/platform_v1/test_goal_functional_checks.py tests/platform_v1/test_functional_execution.py tests/platform_v1/test_goal_configuration.py tests/platform_v1/test_goal_plan_revision.py -q -p no:cacheprovider, and git diff --check. Perform the Issue 776 actual changed-TypeScript client to isolated loopback Task API to disk SQLite/Git/installed-pytest integration, with only model execution and binding metadata as explicit local fakes; verify successful/failed/missing/fixture proof and selection/stale-revision handling with reopened SQLite. Reuse installed tooling and existing test/service seams, retain sanitized evidence outside the repository, and close owned test servers after use. No external network, providers, credentials, local browsers or snapshot updates. Run transition lint, preflight and publication readiness; require passing checks before publication."
    ],
    "github_control_plane_network_exceptions": [
      "After blocking checks pass, push only codex/f03-functional-check-selection-and-evidence and create/update one Draft PR in dddd2024/Nerelan against main at 139baff28ef86ccbe1c5da008bd4dff7f954f68b; publish disclosed audit/evidence and Issue 776/653/659 progress comments; no other branch or repository publication.",
      "Only after disclosed exact-head self-audit, required natural checks, unchanged approved Decision and immediate remote main 139baff28ef86ccbe1c5da008bd4dff7f954f68b, exact reviewed head and CLEAN/MERGEABLE observation, mark the bound PR ready; require natural final State/Landing checks, reobserve immediately and perform one ordinary merge with expected-head protection. Verify merged commit and main and exact parents. This action is explicitly delegated by the user; never claim independent human review."
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
      "command_id": "issue776.bootstrap",
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
      "command_id": "issue776.implement",
      "command": "Implement only the eighteen frontend/test/documentation paths and complete user-facing contract in Issue 776: closed check selection, same-Goal review and safe Task/Run evidence presentation; reuse existing host APIs and installed dependencies. No backend/store/control-plane, workflow, dependency, provider, credential, local browser or reverse-tool change.",
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
        "frontend/src/types/index.ts",
        "frontend/src/lib/platform-client.ts",
        "frontend/src/lib/goal-continuation-operation.ts",
        "frontend/src/lib/task-client.ts",
        "frontend/src/lib/functional-validation.ts",
        "frontend/src/hooks/use-task.ts",
        "frontend/src/hooks/use-tasks.ts",
        "frontend/src/components/goal-review-editor.tsx",
        "frontend/src/components/functional-validation.tsx",
        "frontend/src/components/task-detail.tsx",
        "frontend/src/routes/runs.tsx",
        "frontend/tests/goal-review-editor.test.tsx",
        "frontend/tests/goal-configuration-client.test.ts",
        "frontend/tests/task-status-mapping.test.ts",
        "frontend/tests/runs.test.tsx",
        "frontend/tests/functional-validation.test.tsx",
        "frontend/e2e/functional-validation.spec.ts",
        "docs/functional-validation.md"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "issue776.validate",
      "command": "Run all frontend unit/component tests with the existing npm test script and the existing npm run build production build, without installing dependencies. Run python -B -m pytest tests/platform_v1/test_goal_functional_checks.py tests/platform_v1/test_functional_execution.py tests/platform_v1/test_goal_configuration.py tests/platform_v1/test_goal_plan_revision.py -q -p no:cacheprovider, and git diff --check. Perform the Issue 776 actual changed-TypeScript client to isolated loopback Task API to disk SQLite/Git/installed-pytest integration, with only model execution and binding metadata as explicit local fakes; verify successful/failed/missing/fixture proof and selection/stale-revision handling with reopened SQLite. Reuse installed tooling and existing test/service seams, retain sanitized evidence outside the repository, and close owned test servers after use. No external network, providers, credentials, local browsers or snapshot updates. Run transition lint, preflight and publication readiness; require passing checks before publication.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "trusted_worker",
      "operations": [
        "unit_test",
        "integration_test",
        "build",
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
      "command_id": "issue776.publish",
      "command": "After blocking checks pass, push only codex/f03-functional-check-selection-and-evidence and create/update one Draft PR in dddd2024/Nerelan against main at 139baff28ef86ccbe1c5da008bd4dff7f954f68b; publish disclosed audit/evidence and Issue 776/653/659 progress comments; no other branch or repository publication.",
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
      "command_id": "issue776.audit",
      "command": "Observe natural exact-head CI, Decision Preflight, State Gate, Model Access and Frontend Playwright as naturally triggered by existing filters; compare actual diagnostic failed node IDs with the locked base and perform a separate disclosed self-audit. No rerun or dispatch.",
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
      "command_id": "issue776.landing",
      "command": "Only after disclosed exact-head self-audit, required natural checks, unchanged approved Decision and immediate remote main 139baff28ef86ccbe1c5da008bd4dff7f954f68b, exact reviewed head and CLEAN/MERGEABLE observation, mark the bound PR ready; require natural final State/Landing checks, reobserve immediately and perform one ordinary merge with expected-head protection. Verify merged commit and main and exact parents. This action is explicitly delegated by the user; never claim independent human review.",
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
