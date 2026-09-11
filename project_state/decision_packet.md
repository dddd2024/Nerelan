# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260911_issue788_artifact_handoff_r2_v4",
  "round_id": "round_20260911_issue788_artifact_handoff_r2_v4",
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
  "decision_scope": "F02_EXPLICIT_ACCEPTED_ARTIFACT_HANDOFF",
  "source_issue": 788,
  "parent_issue": 652,
  "repository": "dddd2024/Nerelan",
  "source_issue_body_sha256": "e75f111057046f9a230e47304decbeef6525905ba4e7ab7020c9f6e30f3e31ca",
  "approved_by": "dddd2024 via explicitly delegated Codex owner action",
  "approval_basis": "User expressly authorized project completion, all tools, owner privileges, self-audit and merge in this task. Agent approval is disclosed and is not independent human review.",
  "risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "6c41aae9b9e148c658d3f9dece9ba71338e82611",
  "activation_base_sha": "6c41aae9b9e148c658d3f9dece9ba71338e82611",
  "starting_head": "6c41aae9b9e148c658d3f9dece9ba71338e82611",
  "required_branch": "codex/f02-accepted-artifact-handoff-r2-v4",
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
    "issue_body_sha256": "e75f111057046f9a230e47304decbeef6525905ba4e7ab7020c9f6e30f3e31ca",
    "specification": "Fresh R2 successor for stopped unpublished Issue #784. STOPPED, unpublished. Artifact execution/restart suite: 52 passed; frontend: 406 passed, lint passed. HTTP/admission run: 2 failed, 9 passed, 52 deselected in 58.14s. Both HTTP tests used nonexistent top-level functionalValidation; live handler code exposes frontend_task.functionalValidation. Preserve all assertions, repair only response access after fresh successor activation, and then complete actual TypeScript/HTTP and full acceptance. Activation 43eca724fbe7109cfe2856b6bf2dfeac379426cb and 21 candidate files preserved with hashes; no product commit/push/PR/audit acceptance/Ready/merge. Codex is acting under explicit user owner/self-audit/merge delegation, not claiming independent human review.\n\nAfter this successor's Decision-only activation and PRE_EXECUTION_AUTHORIZED, copy only these 21 candidate files from F:/Nerelan-final-audit-evidence-20260911/issue784-stopped-candidate, verifying SHA256. No old Decision/gates/commits or acceptance inherited. Correct the HTTP test to consume the actual frontend_task.functionalValidation response without removing or weakening any functional assertion. Finish all inherited scope and full checks.\n\n- `reverse_agent/platform_v1/artifact_handoff.py` SHA256 `67586d601efedfcfd9b449bfa45b59e2c0382a8a2372cf77263eaffaab5ff344`\n- `reverse_agent/platform_v1/goal_service.py` SHA256 `6e708bcda0707f5e0ae7fd57850c2aea37db3b11563c65459c708b60f3867f4b`\n- `reverse_agent/platform_v1/run_store.py` SHA256 `5f561a55a0bc6c19ee9a0e9b74ac623b6135602e1aeddc1fb5c4a4d88ed8eacc`\n- `reverse_agent/platform_v1/task_execution.py` SHA256 `7da074b56c23ddc42e5aea97e4ebed7ca1517f15a87bdd2ed0a4ef7f895531cb`\n- `reverse_agent/platform_v1/durable_execution.py` SHA256 `cf8c31a39712dddd7aa88a95235221e4f824bad20e0b3f3e2009af59ca1c123e`\n- `reverse_agent/platform_v1/functional_validation.py` SHA256 `78ffb472b98c35214bd1479d140a34f8aeb23b44476629da928bbde9427e3866`\n- `frontend/src/types/index.ts` SHA256 `87cdf56dae6f23a2cd870f0aa29c665a8ed72c16d77d18fcbd4a545127833f1d`\n- `frontend/src/lib/platform-client.ts` SHA256 `8ae8e0c75ee0e252164b89f44dd44a28c1c5301e199380bb26f15df7d7485bb6`\n- `frontend/src/lib/goal-continuation-operation.ts` SHA256 `bf06f6249808f2d94e6ac70ff1d452f7491f88c5cf2a5f92a9736af0869154f6`\n- `frontend/src/lib/functional-validation.ts` SHA256 `1cebafc7a700e3458d7142779178553102eef5ff25ef7c9832835b55823f6152`\n- `frontend/src/components/goal-review-editor.tsx` SHA256 `a6805510d699a6c38e201ba56b70d63e7eee7162816773d8088f36cdda6af724`\n- `frontend/src/components/functional-validation.tsx` SHA256 `b1cef273c110a406c50127926ae1788d833505b83de6f1b06836bc2d2736afda`\n- `tests/platform_v1/test_artifact_handoff.py` SHA256 `392b464f35bc8cf9842d4bc2d25d4c91dc9e212e721dabebf6505eff4c58b150`\n- `tests/platform_v1/test_artifact_handoff_http.py` SHA256 `692c52408eae62436be01bc722ffb206a3e9e04146bf67e08cf7fc4c2ceb27b8`\n- `tests/platform_v1/test_goal_functional_checks.py` SHA256 `a7a3814d2d5863511f235fc3768978eeda9143e8cab8c3b7b9bede90aff84f7c`\n- `frontend/tests/goal-review-editor.test.tsx` SHA256 `9487107959adf0189298b68f57cf522ef17e5c1c182819cc8587204f88aaf905`\n- `frontend/tests/goal-configuration-client.test.ts` SHA256 `f2a3a25bd03f1566059d0fc622028002bc5bb7cd2d65a51ea4e82475bd0c8835`\n- `frontend/tests/functional-validation.test.tsx` SHA256 `9cfd20baf868507407b4b28a977225f8678ab3cee2530438b0b1291c3ca1d900`\n- `frontend/e2e/artifact-handoff.spec.ts` SHA256 `cdd8a6bf3e4458a2ba329aff8b6bd2a606aac9dab2361a78b15476acf95f3a5f`\n- `docs/artifact-handoff.md` SHA256 `9e9d58a106e5ece3f49b8ffc0abddcbd4f7ead3d65e673fe0b5b93eeefe597bf`\n- `docs/functional-validation.md` SHA256 `512d821607666f6a97c8180a97d843e99cd6e300acee1bb41a42aeb5d7ea809a`\n\nInherited complete implementation scope:\n\nParent F02 #652; overall functional acceptance #659. F03 backend #772 and UI #779 are merged. This candidate is a precise implementation work item, not execution authority. Use the user's existing explicit Owner/self-audit/merge delegation to approve a fresh immutable R2 Decision before source changes. All approval, self-review and publication must be disclosed as Codex actions, not independent human review.\n\nLocked integration base: `main@6c41aae9b9e148c658d3f9dece9ba71338e82611`. Fresh branch: `codex/f02-accepted-artifact-handoff-r2-v4`. No history reuse or changes to preserved old worktrees.\n\nImplement complete explicit cross-Task accepted-artifact handoff, preserving the existing single-Task team default and order-only dependency semantics. Reuse the existing Git object/private-index snapshot/worktree primitives, Goal approval, TaskStore connection/evidence, durable claims/checkpoints and execution services. No second database, execution runner, coordinator or governance Gate/receipt/schema.\n\nApproved plan contract: an optional closed `artifact_input` object with exactly `plan_task_id` selecting one declared dependency from the same Goal/revision. Null/absence means no artifact consumption. Reject malformed/multiple/self/missing/nondependency inputs and cycles. Selected producers and consumers must have executable functional checks; fixture output cannot qualify. Plan saving preserves selection across unrelated edits, explicit clearing removes it, and selection/removal changes the revision/digest and invalidates earlier approval. Render the choice in the reviewable plan and provide a closed dependency selector in the existing plan editor; no implicit selection, automatic approval or launch.\n\nProducer artifact: require the current nonfixture host-verified functional proof binding repository, original approved base, Goal/revision/task/execution/run/lease, contract/result digest and exact accepted private-index tree. Accepted uncommitted edits are part of the artifact: proof.head alone is insufficient. Materialize an immutable Git commit whose tree equals that accepted tree, without staging/changing the producer's real index or worktree. Bound local retention to `refs/nerelan/accepted-artifacts/<task-id>/<execution-id>` with create-if-absent semantics; an existing identical binding is idempotent, any mismatch rejects. Never update unrelated refs or remote refs. Persist the exact commit/tree/producer proof identity in existing TaskStore evidence; deterministic retries and crash seams must not replace an accepted binding. Do not use a later moving producer directory or textual diff replay as accepted identity.\n\nConsumer admission: before executor dispatch, resolve the explicit producer from the same approved Goal revision/repository, verify its current accepted proof and retained Git objects, and persist once the consumed identity under the consumer execution/lease. Use the existing trusted OpenCode base_ref and detached worktree preparation from that exact commit. Preserve original approved repository_base_sha separately from prepared input HEAD; never overwrite the frozen functional contract. Reject old/missing/changed input, wrong repository/revision/execution, inaccessible objects, stale lease and unsupported conflicting/multiple outputs. No shared-folder inference or automatic merge of producer branches.\n\nAcceptance semantics: an input-consuming validate_task must test exactly the producer's accepted tree; modifying it rejects acceptance. An execute_task consumer may intentionally produce a new artifact derived from the explicit input. Apply the same input contract to ordinary and durable single/sequential-team execution and all restart paths. Resume validates persisted input/checkpoint identity before additional work; retries cannot overwrite existing worktrees, apply patches twice or redispatch an ambiguous external operation. Safe Task/Run functional evidence shows consumed producer/commit/tree/result identities and verification/failure reason without credentials, raw output, environment or arbitrary command data.\n\nRequired acceptance:\n- A creates unique behavior in a real temporary Git repository; B's actual installed pytest check reads the same accepted tree, including initially uncommitted edits.\n- Old baseline, missing proof/object, changed artifact, wrong repository/revision/execution and fixture/failed/zero-test proof reject; a validate_task that changes accepted input rejects.\n- Parallel incompatible outputs never combine implicitly. Restart/retry across preparation, retention, TaskStore persistence and checkpoint seams preserves input identity; stale owners cannot bind or replace it.\n- Real disk SQLite reopen proves immutable producer/consumer identity and approved revision/digest. Keep the existing dependency-before-LIMIT scheduler and single-Task role behavior.\n- Changed TypeScript client -> isolated loopback Task API -> SQLite/Git/pytest acceptance covers explicit selection/removal/approval/launch and safe evidence. Only model execution and binding metadata may be disclosed test doubles. Local browser/provider/model/credential calls remain forbidden; natural existing CI Playwright may test the frontend under existing workflow filters.\n- All scoped regression tests, frontend lint/unit/build and diff checks pass on the final exact head. Compare actual natural full diagnostic failure nodes to the actual locked-base diagnostic; no new failures, no deleted assertions/skips/deselections to hide a regression.\n\nExact allowed product paths (new files only where named):\n\n```text\nreverse_agent/platform_v1/artifact_handoff.py\nreverse_agent/platform_v1/goal_service.py\nreverse_agent/platform_v1/run_store.py\nreverse_agent/platform_v1/task_execution.py\nreverse_agent/platform_v1/durable_execution.py\nreverse_agent/platform_v1/functional_validation.py\nfrontend/src/types/index.ts\nfrontend/src/lib/platform-client.ts\nfrontend/src/lib/goal-continuation-operation.ts\nfrontend/src/lib/functional-validation.ts\nfrontend/src/components/goal-review-editor.tsx\nfrontend/src/components/functional-validation.tsx\ntests/platform_v1/test_artifact_handoff.py\ntests/platform_v1/test_artifact_handoff_http.py\ntests/platform_v1/test_goal_functional_checks.py\ntests/platform_v1/test_goal_service.py\ntests/platform_v1/test_functional_execution.py\ntests/platform_v1/test_durable_execution.py\ntests/platform_v1/test_durable_execution_v5.py\ntests/platform_v1/test_task_execution.py\nfrontend/tests/goal-review-editor.test.tsx\nfrontend/tests/goal-configuration-client.test.ts\nfrontend/tests/functional-validation.test.tsx\nfrontend/e2e/artifact-handoff.spec.ts\ndocs/artifact-handoff.md\ndocs/functional-validation.md\n```\n\nRequired deterministic checks:\n\n```text\npython -B -m pytest tests/platform_v1/test_artifact_handoff.py tests/platform_v1/test_artifact_handoff_http.py tests/platform_v1/test_goal_service.py tests/platform_v1/test_goal_functional_checks.py tests/platform_v1/test_goal_configuration.py tests/platform_v1/test_goal_plan_revision.py tests/platform_v1/test_functional_validation.py tests/platform_v1/test_functional_execution.py tests/platform_v1/test_durable_execution.py tests/platform_v1/test_durable_execution_v5.py tests/platform_v1/test_task_execution.py tests/platform_v1/test_repository_workspace.py -q -p no:cacheprovider\nnpm run lint\nnpm test\nnpm run build\ngit diff --check\n```\n\nReuse installed dependencies only; run npm commands from frontend. Additional focused runs within these approved test files and tests authored in the two named new backend files are permitted while implementing; run the complete required list before publication. External loopback probes and pytest-owned temporary Git/SQLite artifacts must remain outside tracked repository paths. Bounded product-managed artifact refs are local only and do not authorize task_branch_publish or any remote Git transport (#643 remains separate).\n\nForbidden: AGENTS/workflow/dependency/lockfile/snapshot/control-plane/project-gate/mainline-schema changes; installation; live models/providers/credentials; local browser execution; binary/reverse tooling; arbitrary network; direct main push; force/rebase/amend/history rewrite; destructive cleanup; auto-merge/tag/release/deploy; runner/workflow dispatch or rerun. Preserve known baseline diagnostic debt and all old worktrees.\n\nPath B must bind the exact source Issue body digest, this base/branch, all product paths plus existing Decision/gate files, and the full contract before implementation. Activate Decision first; require existing startup/command-plan/lint/preflight PRE_EXECUTION_AUTHORIZED and publication readiness. Publish only this branch and one Draft to the locked main after validation. Record actual natural checks, perform a separate disclosed exact-head self-audit and use the existing separately bound false/none landing authority and premerge attestation protocol before expected-head ordinary Ready/merge. Parent #652/#659 cannot close until their full acceptance is actually proven.\n"
  },
  "predecessor_issue": 784,
  "predecessor_status": "STOPPED_UNPUBLISHED_FOCUSED_TEST_FAILURE",
  "candidate_file_copy_only": true,
  "artifact_retention_ref_prefix": "refs/nerelan/accepted-artifacts/",
  "artifact_retention_create_only": true,
  "artifact_retention_identical_binding_noop_allowed": true,
  "artifact_retention_remote_publication_allowed": false,
  "artifact_input_original_base_immutable": true,
  "validate_task_input_tree_immutable": true,
  "local_browser_execution_allowed": false,
  "provider_free_acceptance_required": true,
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
    "reverse_agent/platform_v1/artifact_handoff.py",
    "reverse_agent/platform_v1/goal_service.py",
    "reverse_agent/platform_v1/run_store.py",
    "reverse_agent/platform_v1/task_execution.py",
    "reverse_agent/platform_v1/durable_execution.py",
    "reverse_agent/platform_v1/functional_validation.py",
    "frontend/src/types/index.ts",
    "frontend/src/lib/platform-client.ts",
    "frontend/src/lib/goal-continuation-operation.ts",
    "frontend/src/lib/functional-validation.ts",
    "frontend/src/components/goal-review-editor.tsx",
    "frontend/src/components/functional-validation.tsx",
    "tests/platform_v1/test_artifact_handoff.py",
    "tests/platform_v1/test_artifact_handoff_http.py",
    "tests/platform_v1/test_goal_functional_checks.py",
    "tests/platform_v1/test_goal_service.py",
    "tests/platform_v1/test_functional_execution.py",
    "tests/platform_v1/test_durable_execution.py",
    "tests/platform_v1/test_durable_execution_v5.py",
    "tests/platform_v1/test_task_execution.py",
    "frontend/tests/goal-review-editor.test.tsx",
    "frontend/tests/goal-configuration-client.test.ts",
    "frontend/tests/functional-validation.test.tsx",
    "frontend/e2e/artifact-handoff.spec.ts",
    "docs/artifact-handoff.md",
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
    "reverse_agent/platform_v1/artifact_handoff.py",
    "reverse_agent/platform_v1/goal_service.py",
    "reverse_agent/platform_v1/run_store.py",
    "reverse_agent/platform_v1/task_execution.py",
    "reverse_agent/platform_v1/durable_execution.py",
    "reverse_agent/platform_v1/functional_validation.py",
    "frontend/src/types/index.ts",
    "frontend/src/lib/platform-client.ts",
    "frontend/src/lib/goal-continuation-operation.ts",
    "frontend/src/lib/functional-validation.ts",
    "frontend/src/components/goal-review-editor.tsx",
    "frontend/src/components/functional-validation.tsx",
    "tests/platform_v1/test_artifact_handoff.py",
    "tests/platform_v1/test_artifact_handoff_http.py",
    "tests/platform_v1/test_goal_functional_checks.py",
    "tests/platform_v1/test_goal_service.py",
    "tests/platform_v1/test_functional_execution.py",
    "tests/platform_v1/test_durable_execution.py",
    "tests/platform_v1/test_durable_execution_v5.py",
    "tests/platform_v1/test_task_execution.py",
    "frontend/tests/goal-review-editor.test.tsx",
    "frontend/tests/goal-configuration-client.test.ts",
    "frontend/tests/functional-validation.test.tsx",
    "frontend/e2e/artifact-handoff.spec.ts",
    "docs/artifact-handoff.md",
    "docs/functional-validation.md"
  ],
  "reference_paths": [
    "reverse_agent/executor_neutral/core.py",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/platform_v1/control_store.py",
    "reverse_agent/platform_v1/unattended_coordinator.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/run_read_model.py"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md",
    ".github/**",
    ".codex-skills/**",
    "reverse_agent/control_plane/**",
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
      "python -B -m pytest tests/platform_v1/test_artifact_handoff.py tests/platform_v1/test_artifact_handoff_http.py tests/platform_v1/test_goal_service.py tests/platform_v1/test_goal_functional_checks.py tests/platform_v1/test_goal_configuration.py tests/platform_v1/test_goal_plan_revision.py tests/platform_v1/test_functional_validation.py tests/platform_v1/test_functional_execution.py tests/platform_v1/test_durable_execution.py tests/platform_v1/test_durable_execution_v5.py tests/platform_v1/test_task_execution.py tests/platform_v1/test_repository_workspace.py -q -p no:cacheprovider\nnpm run lint\nnpm test\nnpm run build\ngit diff --check\nPerform real temporary Git producer-consumer and diskSQLite reopen/restart/race tests, plus actual changed-TypeScript client to isolated loopback TaskAPI to diskSQLite/Git/installed-pytest acceptance. Only model execution and binding metadata may be disclosed local doubles. Reuse installed tooling and existing test/service seams, retain sanitized evidence outside tracked repository paths and close owned servers. No external network, providers, credentials, local browser, installation or snapshot update. Run existing transition-lint/preflight and publication-readiness; require all complete checks on exact head before publication."
    ],
    "ci_network_exceptions": [],
    "trusted_worker_network_exceptions": [
      "python -B -m pytest tests/platform_v1/test_artifact_handoff.py tests/platform_v1/test_artifact_handoff_http.py tests/platform_v1/test_goal_service.py tests/platform_v1/test_goal_functional_checks.py tests/platform_v1/test_goal_configuration.py tests/platform_v1/test_goal_plan_revision.py tests/platform_v1/test_functional_validation.py tests/platform_v1/test_functional_execution.py tests/platform_v1/test_durable_execution.py tests/platform_v1/test_durable_execution_v5.py tests/platform_v1/test_task_execution.py tests/platform_v1/test_repository_workspace.py -q -p no:cacheprovider\nnpm run lint\nnpm test\nnpm run build\ngit diff --check\nPerform real temporary Git producer-consumer and diskSQLite reopen/restart/race tests, plus actual changed-TypeScript client to isolated loopback TaskAPI to diskSQLite/Git/installed-pytest acceptance. Only model execution and binding metadata may be disclosed local doubles. Reuse installed tooling and existing test/service seams, retain sanitized evidence outside tracked repository paths and close owned servers. No external network, providers, credentials, local browser, installation or snapshot update. Run existing transition-lint/preflight and publication-readiness; require all complete checks on exact head before publication."
    ],
    "github_control_plane_network_exceptions": [
      "After blocking checks pass, push only codex/f02-accepted-artifact-handoff-r2-v4 and create/update one Draft PR in dddd2024/Nerelan against main at 6c41aae9b9e148c658d3f9dece9ba71338e82611; publish disclosed audit/evidence and Issue 788/652/659 progress comments; no other branch or repository publication.",
      "Only after disclosed exact-head self-audit, required natural checks, unchanged approved Decision and immediate remote main 6c41aae9b9e148c658d3f9dece9ba71338e82611, exact reviewed head and CLEAN/MERGEABLE observation, mark the bound PR ready; require natural final State/Landing checks, reobserve immediately and perform one ordinary merge with expected-head protection. Verify merged commit and main and exact parents. This action is explicitly delegated by the user; never claim independent human review."
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
      "command_id": "issue788.bootstrap",
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
      "command_id": "issue788.implement",
      "command": "After fresh activation/preflight, copy only the twenty-one hash-bound product candidate files from preserved stopped Issue784 as specified in Issue788, never old Decision/gates/commits. Correct only the HTTP test response access to frontend_task.functionalValidation, retaining every functional assertion; finish the complete implementation and all acceptance checks. Preserve validation-only skipped roles, implementation diff requirements, original-base/input-head distinction and all negative/restart coverage. Implement the complete F02 explicit accepted-artifact input contract and exactly twenty-six source/frontend/test/documentation paths in Issue788. Reuse existing Git object/private-index/worktree preparation, TaskStore evidence/lease/checkpoints and all ordinary/durable single/team execution and recovery paths. Preserve frozen approved base separately from exact producer input commit/tree. Include validation-only immutability, UI selection/review and safe consumed-input evidence. Bounded local retention refs/nerelan/accepted-artifacts/<task-id>/<execution-id> use create-if-absent with identical-binding idempotence only, no remote publication or arbitrary ref mutation. No second database, runner, coordinator or Gate; no workflow/dependency/provider/credential/browser/reverse-tool change.",
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
        "reverse_agent/platform_v1/artifact_handoff.py",
        "reverse_agent/platform_v1/goal_service.py",
        "reverse_agent/platform_v1/run_store.py",
        "reverse_agent/platform_v1/task_execution.py",
        "reverse_agent/platform_v1/durable_execution.py",
        "reverse_agent/platform_v1/functional_validation.py",
        "frontend/src/types/index.ts",
        "frontend/src/lib/platform-client.ts",
        "frontend/src/lib/goal-continuation-operation.ts",
        "frontend/src/lib/functional-validation.ts",
        "frontend/src/components/goal-review-editor.tsx",
        "frontend/src/components/functional-validation.tsx",
        "tests/platform_v1/test_artifact_handoff.py",
        "tests/platform_v1/test_artifact_handoff_http.py",
        "tests/platform_v1/test_goal_functional_checks.py",
        "tests/platform_v1/test_goal_service.py",
        "tests/platform_v1/test_functional_execution.py",
        "tests/platform_v1/test_durable_execution.py",
        "tests/platform_v1/test_durable_execution_v5.py",
        "tests/platform_v1/test_task_execution.py",
        "frontend/tests/goal-review-editor.test.tsx",
        "frontend/tests/goal-configuration-client.test.ts",
        "frontend/tests/functional-validation.test.tsx",
        "frontend/e2e/artifact-handoff.spec.ts",
        "docs/artifact-handoff.md",
        "docs/functional-validation.md"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "issue788.validate",
      "command": "python -B -m pytest tests/platform_v1/test_artifact_handoff.py tests/platform_v1/test_artifact_handoff_http.py tests/platform_v1/test_goal_service.py tests/platform_v1/test_goal_functional_checks.py tests/platform_v1/test_goal_configuration.py tests/platform_v1/test_goal_plan_revision.py tests/platform_v1/test_functional_validation.py tests/platform_v1/test_functional_execution.py tests/platform_v1/test_durable_execution.py tests/platform_v1/test_durable_execution_v5.py tests/platform_v1/test_task_execution.py tests/platform_v1/test_repository_workspace.py -q -p no:cacheprovider\nnpm run lint\nnpm test\nnpm run build\ngit diff --check\nPerform real temporary Git producer-consumer and diskSQLite reopen/restart/race tests, plus actual changed-TypeScript client to isolated loopback TaskAPI to diskSQLite/Git/installed-pytest acceptance. Only model execution and binding metadata may be disclosed local doubles. Reuse installed tooling and existing test/service seams, retain sanitized evidence outside tracked repository paths and close owned servers. No external network, providers, credentials, local browser, installation or snapshot update. Run existing transition-lint/preflight and publication-readiness; require all complete checks on exact head before publication.",
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
      "command_id": "issue788.publish",
      "command": "After blocking checks pass, push only codex/f02-accepted-artifact-handoff-r2-v4 and create/update one Draft PR in dddd2024/Nerelan against main at 6c41aae9b9e148c658d3f9dece9ba71338e82611; publish disclosed audit/evidence and Issue 788/652/659 progress comments; no other branch or repository publication.",
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
      "command_id": "issue788.audit",
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
      "command_id": "issue788.landing",
      "command": "Only after disclosed exact-head self-audit, required natural checks, unchanged approved Decision and immediate remote main 6c41aae9b9e148c658d3f9dece9ba71338e82611, exact reviewed head and CLEAN/MERGEABLE observation, mark the bound PR ready; require natural final State/Landing checks, reobserve immediately and perform one ordinary merge with expected-head protection. Verify merged commit and main and exact parents. This action is explicitly delegated by the user; never claim independent human review.",
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
