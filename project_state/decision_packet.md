# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260912_issue833_visible_goal_evidence_r3_v1",
  "round_id": "round_20260912_issue833_visible_goal_evidence_r3_v1",
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
  "decision_scope": "F03_VISIBLE_GOAL_EVIDENCE_REAL_EDGE",
  "source_issue": 833,
  "parent_issue": 653,
  "repository": "dddd2024/Nerelan",
  "source_issue_body_sha256": "36826a484bf934dd57bdacf6de942cbf191a25e593f4afad0e0e4f422ff83559",
  "approved_by": "dddd2024 via explicitly delegated Codex owner action",
  "approval_basis": "The user explicitly delegated Owner authority, self-audit, merge and all tools for project completion. This is disclosed Codex approval, not independent human review.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R2",
  "workflow_profile": "browser_r3",
  "integration_base_ref": "main",
  "base_sha": "1b87cb41606bfbda0b4b49dd18259550fbf5bb58",
  "activation_base_sha": "1b87cb41606bfbda0b4b49dd18259550fbf5bb58",
  "starting_head": "1b87cb41606bfbda0b4b49dd18259550fbf5bb58",
  "required_branch": "codex/f03-visible-goal-evidence-r3-v1",
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
  "product_change_commit_limit": 4,
  "generated_governance_commit_limit": 2,
  "normal_push_attempt_limit": 3,
  "draft_pr_creation_limit": 3,
  "transport_total_attempt_limit": 3,
  "successful_branch_publication_limit": 1,
  "successful_draft_pr_creation_limit": 1,
  "transport_retry_requires_confirmed_no_remote_mutation": true,
  "mark_ready_attempt_limit": 1,
  "merge_attempt_limit": 1,
  "dependency_install_limit": 0,
  "workflow_rerun_limit": 0,
  "workflow_dispatch_limit": 0,
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
  "expected_head_protection_required": true,
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
  "known_browser_execution_allowed": true,
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "no_legacy_intent_mode": "READ_ONLY_LANDING_CANDIDATE_VALIDATION",
  "landing_authority_scope_note": "This Decision allows only its exact branch PR to follow the separately bound existing Owner landing authority protocol after full real-browser and natural exact-head acceptance; false/none alone grants no mutation.",
  "semantic_implementation_contract": {
    "issue_body_sha256": "36826a484bf934dd57bdacf6de942cbf191a25e593f4afad0e0e4f422ff83559",
    "specification": "CANDIDATE R3 Work Item for remaining F03 visible Goal evidence and actual Edge acceptance. This Issue alone is not execution authority; activate an immutable APPROVED R3 Decision under the user's explicit Owner/self-audit/merge delegation. All such approval/audit/landing actions are disclosed Codex actions, not independent human review.\n\nParent: F03 #653. Locked base: main@1b87cb41606bfbda0b4b49dd18259550fbf5bb58, the ordinary merge of accepted backend Goal proof PR827. Exact branch: codex/f03-visible-goal-evidence-r3-v1. Native mainline receipt is EMITTED/PASSED; main CI34671618527 and State34671618526 succeeded on this base. Actual diagnostic22 failed6327 passed23 skipped1warning has exactly the same22base failure nodes and no new failure. Source826 was completed by Owner with comment5643441247 and closure2026-09-12T04:26:09Z; do not reopen or repeat its closure. No prior branch/history is reused.\n\nThe backend now supplies coherent current task identity, executor provenance, functional proof and bounded publication records for Goal list/detail/page. The UI must make these facts visible and distinguish execution ended, functional verification, pending review, recorded Draft publication and unobserved remote merge/delivery. Goal COMPLETED and Task READY_FOR_REVIEW are not functional verification by themselves.\n\nImplementation contract:\n\n- Reuse the existing PlatformGoal/Run publication types, normalizeFunctionalValidation and FunctionalValidationView. Add the optional Goal proof fields and share a compact presentation label if needed; do not add a second verifier or execution store. A positive badge requires complete current host proof and explicit real-executor provenance. Missing/malformed/stale/failed/zero-test proof must not become verified. Fixture status/provenance must remain visibly distinct even when malformed test input claims real success.\n- GoalProgress shows readable execution/review state and functional status. Detailed checks, actual counts, contract/result digests and exact base/head/tree remain inspectable through the existing proof component. Keep important status visible outside collapsed evidence. Add accessible exact Run links only for materialized task_links; unlaunched plan IDs are not runtime Task IDs. Preserve interrupted recovery controls, dependencies, ordering and progress semantics.\n- Reuse truthful wording from immutable PR819 head477ce00ac161dbc28337b73f646521ff18398be7 where applicable, after checking its actual disposition and the source hunks. Its six paths overlap this scope, but its old Decision/base/history are not authority for this round. Preserve that branch and Draft. Do not hide meaningful status solely to preserve existing screenshots.\n- Home/review Goal COMPLETED labels and derived Roadmap phase/member labels say execution ended/pending acceptance rather than imply functional delivery. Roadmap remains a projection of Goal truth. Recorded publication PENDING/COMMIT_CREATED/PUSHED/COMPLETE/FAILED is separate; COMPLETE means recorded Draft creation, while current remote review/merge is not observed. A recorded PR link is not proof that the remote PR is still Draft or merged.\n- Keep keyboard navigation, mobile wrapping, readable status and existing styles. No unrelated redesign, backend change or snapshot replacement. No browser shell/filesystem/credential/policy authority.\n\nExact product allowlist:\n\n```text\nfrontend/src/lib/platform-client.ts\nfrontend/src/lib/functional-validation.ts\nfrontend/src/components/functional-validation.tsx\nfrontend/src/components/goal-progress.tsx\nfrontend/src/routes/home.tsx\nfrontend/src/routes/approvals.tsx\nfrontend/src/routes/roadmap.tsx\nfrontend/tests/platform-home.test.tsx\nfrontend/tests/task-first-lifecycle-states.test.tsx\nfrontend/tests/approvals.test.tsx\nfrontend/tests/roadmap.test.tsx\nfrontend/tests/functional-validation.test.tsx\nfrontend/tests/goal-completion-evidence.test.tsx\nfrontend/e2e/functional-validation.spec.ts\ndocs/functional-validation.md\n```\n\nThe Decision may additionally allow only its immutable project_state/decision_packet.md and the five existing generated gates used by current product rounds. No backend, workflow, dependency/lockfile, schema, validator, database migration or new artifact family is authorized. Preserve existing dirty/stopped worktrees.\n\nRequired deterministic and user-flow acceptance:\n\n1. All existing frontend unit/component tests, npm run lint and production build. Add meaningful Goal rendering/deep-link tests for actual valid/failed/missing/stale/zero/fixture evidence, publication independence, complete/malformed proof, updated server responses and unmaterialized plan rows. Retain existing functional, lifecycle, recovery and accessibility assertions.\n2. Existing backend regressions: tests/platform_v1/test_goal_completion_evidence.py, tests/platform_v1/test_goal_service.py and tests/platform_v1/test_run_read_model.py, plus git diff --check and existing immutable Decision plan/lint/preflight/publication-readiness gates.\n3. Under a separately explicit user_local machine-specific R3 command, run an isolated real Vite frontend and real Task API on loopback, backed by temporary disk SQLite/Git and installed pytest. Seed executions through the existing Goal/test/service seams: valid single and sequential-team, syntax error, failed assertion, no implementation, zero executed tests, missing/stale proof and actual deterministic fixture. Only model execution and binding metadata may be disclosed doubles. Browser-visible Goal proof and exact Run links must agree with actual HTTP and reopened SQLite identities/digests. Confined corruption of a disposable fixture DB may test stale/missing evidence; never alter product runtime state. A synthetic recorded Draft tests presentation only and must not be described as real GitHub publication. Real provider/desktop and #135 publication acceptance remain separate.\n4. Known installed Edge may run only with a temporary profile, headless by default, no personal browser data and loopback-only application requests. Use the installed Playwright1.62.1 library. Read and verify executable provenance before launch; observed candidate is C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe, version153.0.4234.32, SHA25681ee5ff42fcec883312170606b10ebbb2b01f5b4cddc2cf485290e40c15b027d. Current Node path E:/Program Files/nodejs/node.exe and Python C:/Program Files/Python313/python.exe are installed. Existing frontend dependencies resolve through F:/Nerelan-issue799-artifact-handoff-v5/frontend/node_modules to F:/reverse-agent-issue585-desktop0-tauri-r2-v9/frontend/node_modules; verify current manifests/lock compatibility before bounded reuse. A junction to those existing dependencies is permitted only as ignored local tooling; do not install/update packages or stage the junction/cache. No package/browser installation or container/WSL startup. Track owned server/browser PIDs and close only those owned processes after acceptance, without broad termination/deletion.\n5. Capture and inspect desktop/mobile and light/dark browser evidence for the changed Goal flow. This Windows Edge functional/visual inspection does not replace Ubuntu Chromium golden acceptance. Require all naturally triggered exact-head CI, Decision Preflight, State Gate, Model Access and Frontend Playwright checks. Do not rerun/dispatch workflows, weaken assertions or update snapshots in this first round.\n6. If the visible change makes an existing golden fail, preserve the failed head/run and actual/expected/diff artifacts and stop that round. A fresh R3 successor may bind only reviewed exact Ubuntu candidate PNG hashes and affected home snapshot paths; no blind refresh or Windows PNG substitution. Do not suppress meaningful UI changes to avoid this acceptance.\n7. Separate disclosed exact-head self-audit, reviewable Draft and existing bounded landing-authority/attestation protocol are required before any Ready/merge. Preserve expected-head ordinary merge protection and immediate no-drift checks. F03 #653 remains open until its complete user-visible acceptance is proved; #659 and the full G0-G6 project goal remain open.\n\nThe fresh Decision must declare browser testing using existing operations machine_specific_execution + integration_test on user_local, with exact loopback bounds and user_local_network_exceptions. browser_execution is not an existing command operation and must not be invented. Set the appropriate browser R3 workflow profile after checking the current schema. Known Edge execution is explicitly granted only by that fresh Decision; current #828 R2 authority does not grant it.\n\nForbidden: provider/model calls, credential/auth-store access, external navigation or publication from the browser, unknown binary execution, dependency installation, snapshots in this round, main push, force push/rebase/squash/amend, automatic merge, tag/release/deploy, runner/workflow dispatch, destructive cleanup, new Gate/receipt/authority store, and any out-of-allowlist product edit. Any blocking check failure or authority/base/head drift stops the round; no fix-forward or silent scope expansion.\n\n\nMachine-specific limits for the fresh Decision: Vite listens only at http://127.0.0.1:5175; the owned Task API binds an ephemeral 127.0.0.1 port and accepts that exact frontend origin. Pass the actual API address through existing VITE_TASK_API_BASE. No browser mock API may substitute for the real acceptance path. Browser application requests are restricted to these owned loopback endpoints; disable background networking where supported and use no personal profile. At most four owned Edge launches, each bounded to30minutes; at most64 PNG screenshots. Owned servers have bounded lifetime and are stopped gracefully; no broad process termination or recursive deletion. Keep isolated profiles/SQLite/Git/worktrees, traces and sanitized evidence under an issue-specific external validation directory. Reobserve Edge SHA256 immediately before launch; mismatch requires renewed explicit authority.\n\nCommit/publication limits: one Decision-only activation before any product change, at most four product commits and two generated-governance commits, one successful initial branch publication and one Draft creation. At most three transport attempts only after readback proves no remote mutation; after successful push no further push under this first round. Validate the exact implementation head before its sole successful publication. No workflow rerun/dispatch. Source/parent/overall progress and a disclosed exact-head self-review may be posted only to this Work Item, its eventual exact Draft, #653 and #659 under the fresh Decision. Do not mutate PR819 or other active work."
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
    "frontend/src/lib/platform-client.ts",
    "frontend/src/lib/functional-validation.ts",
    "frontend/src/components/functional-validation.tsx",
    "frontend/src/components/goal-progress.tsx",
    "frontend/src/routes/home.tsx",
    "frontend/src/routes/approvals.tsx",
    "frontend/src/routes/roadmap.tsx",
    "frontend/tests/platform-home.test.tsx",
    "frontend/tests/task-first-lifecycle-states.test.tsx",
    "frontend/tests/approvals.test.tsx",
    "frontend/tests/roadmap.test.tsx",
    "frontend/tests/functional-validation.test.tsx",
    "frontend/tests/goal-completion-evidence.test.tsx",
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
    "frontend/src/lib/platform-client.ts",
    "frontend/src/lib/functional-validation.ts",
    "frontend/src/components/functional-validation.tsx",
    "frontend/src/components/goal-progress.tsx",
    "frontend/src/routes/home.tsx",
    "frontend/src/routes/approvals.tsx",
    "frontend/src/routes/roadmap.tsx",
    "frontend/tests/platform-home.test.tsx",
    "frontend/tests/task-first-lifecycle-states.test.tsx",
    "frontend/tests/approvals.test.tsx",
    "frontend/tests/roadmap.test.tsx",
    "frontend/tests/functional-validation.test.tsx",
    "frontend/tests/goal-completion-evidence.test.tsx",
    "frontend/e2e/functional-validation.spec.ts",
    "docs/functional-validation.md"
  ],
  "reference_paths": [
    "reverse_agent/platform_v1/goal_service.py",
    "reverse_agent/platform_v1/run_read_model.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/functional_validation.py",
    "tests/platform_v1/test_goal_completion_evidence.py",
    "tests/platform_v1/test_functional_execution.py",
    "tests/platform_v1/test_goal_functional_checks.py"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md",
    ".github/**",
    ".codex-skills/**",
    "reverse_agent/**",
    "tests/**",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/e2e/snapshots/**",
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
    "squash",
    "amend",
    "reset",
    "clean",
    "stash",
    "restore",
    "tag_or_release",
    "runner_dispatch",
    "model_api_invocation",
    "external_reverse_tool_invocation",
    "unknown_binary_execution",
    "destructive",
    "snapshot_update",
    "dependency_install",
    "workflow_dispatch",
    "workflow_rerun",
    "active_json_rewrite",
    "personal_browser_profile",
    "arbitrary_external_navigation",
    "duplicate_remote_mutation"
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
    "trusted_worker_network_exceptions": [
      "Run existing npm test, npm run lint and npm run build without dependency installation. Run python -B -m pytest tests/platform_v1/test_goal_completion_evidence.py tests/platform_v1/test_goal_service.py tests/platform_v1/test_run_read_model.py -q -p no:cacheprovider and git diff --check. Backend tests may use only their existing isolated loopback Git/SQLite/pytest seams and explicit local model/binding doubles, zero provider calls. Run existing immutable Decision gates and publication readiness on the exact committed implementation head. All blocking checks must pass before publication; preserve any failed round without fix-forward."
    ],
    "github_control_plane_network_exceptions": [
      "After all exact-head local and real browser checks pass, push onlycodex/f03-visible-goal-evidence-r3-v1 todddd2024/Nerelan and create exactly one Draft against main@1b87cb41606bfbda0b4b49dd18259550fbf5bb58. One successful push and one successful Draft only; at most3 transport attempts overall, only after readback confirms no mutation. After successful push no further push. Publish disclosed review/evidence and bounded progress comments only to Issue833, its exact Draft,653 and659. Do not mutate other branches/Issues/PRs or repeat completed826 closure.",
      "Only after separate disclosed exact-head self-audit, all required natural checks, current unchanged approved Decision/base/head and separately bound immutable landing authority with its own checks, use the existing false/none Owner landing protocol for the exact Issue833 Draft. Require NEW Ready-triggered formal landing-state-gate, existing premerge attestation, live required contexts and immediate main==1b87cb41606bfbda0b4b49dd18259550fbf5bb58, CLEAN/MERGEABLE and no concurrent target mutation. At most one Ready and one ordinary method=merge with expected-head protection; verify actual parents/tree/main and native mainline receipt. No independent human review claim or direct main push."
    ],
    "user_local_network_exceptions": [
      "On user_local only, use machine-specific installed Edge153.0.4234.32 at C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe, SHA25681ee5ff42fcec883312170606b10ebbb2b01f5b4cddc2cf485290e40c15b027d, and installed Playwright1.62.1. Verify executable hash before launch. Run the actual changed Vite frontend only at http://127.0.0.1:5175 and an owned real Task API at one ephemeral127.0.0.1 port with that exact Origin; use existing VITE_TASK_API_BASE. All application requests must remain on those loopback endpoints. Use isolated browser profiles, headless by default, no personal profile and disable background networking where supported. At most4 Edge launches, each at most30minutes, and64 PNG screenshots. Actual Git/SQLite/installed-pytest fixtures must cover valid single/team, syntax error, failed assertion, no implementation, zero tests, missing/stale evidence and actual deterministic fixture. Only model execution and binding metadata are disclosed doubles. Verify browser-visible Goal proof and exact Run navigation against HTTP and reopened SQLite identities/digests. Keep recorded-Draft presentation fixtures separate from real remote publication; do not visit external PR links. Inspect desktop/mobile light/dark captures and keyboard interactions. Retain sanitized artifacts under F:/Nerelan-final-audit-evidence-20260911/issue833-browser, use temporary test Git/SQLite/worktrees there, track owned PIDs, and close only owned test browser/server processes gracefully. No broad termination/deletion, providers, credentials, external navigation, installs, WSL/container startup or snapshot update. Any blocking failure or executable/authority mismatch stops this round."
    ]
  },
  "path_risk_floor": [
    {
      "pattern": "project_state/**",
      "minimum_risk": "R2"
    }
  ],
  "allowed_commands": [
    {
      "command_id": "issue833.bootstrap",
      "command": "Observe main exactly1b87cb41606bfbda0b4b49dd18259550fbf5bb58, accepted PR827 native receipt/main CI and fresh clean branchcodex/f03-visible-goal-evidence-r3-v1; commit this immutable APPROVED R3 Decision alone as the first activation commit. Run existing startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre and worktree-publication-readiness. Require PRE_EXECUTION_AUTHORIZED and PUBLICATION_READY before product mutation or any browser/server launch. Do not copy prior Decision/gates/history.",
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
      "command_id": "issue833.implement",
      "command": "Implement only the15 named frontend/test/docs paths in Issue833: current Goal functional proof, explicit execution/review/publication/remote-acceptance distinctions, exact materialized Task Run links and truthful derived Roadmap labels. Reuse existing normalizer/view/TaskStore API and immutable truthful PR819 hunks where applicable; preserve819 and all other branches. No backend, workflow, dependency, schema, validator or snapshot edits. Existing dependency junction reuse is permitted only as ignored tooling after manifest/lock verification, never staged. Keep meaningful status visible and mobile/keyboard interaction usable.",
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
        "frontend/src/lib/platform-client.ts",
        "frontend/src/lib/functional-validation.ts",
        "frontend/src/components/functional-validation.tsx",
        "frontend/src/components/goal-progress.tsx",
        "frontend/src/routes/home.tsx",
        "frontend/src/routes/approvals.tsx",
        "frontend/src/routes/roadmap.tsx",
        "frontend/tests/platform-home.test.tsx",
        "frontend/tests/task-first-lifecycle-states.test.tsx",
        "frontend/tests/approvals.test.tsx",
        "frontend/tests/roadmap.test.tsx",
        "frontend/tests/functional-validation.test.tsx",
        "frontend/tests/goal-completion-evidence.test.tsx",
        "frontend/e2e/functional-validation.spec.ts",
        "docs/functional-validation.md"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "issue833.validate",
      "command": "Run existing npm test, npm run lint and npm run build without dependency installation. Run python -B -m pytest tests/platform_v1/test_goal_completion_evidence.py tests/platform_v1/test_goal_service.py tests/platform_v1/test_run_read_model.py -q -p no:cacheprovider and git diff --check. Backend tests may use only their existing isolated loopback Git/SQLite/pytest seams and explicit local model/binding doubles, zero provider calls. Run existing immutable Decision gates and publication readiness on the exact committed implementation head. All blocking checks must pass before publication; preserve any failed round without fix-forward.",
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
      "command_id": "issue833.browser",
      "command": "On user_local only, use machine-specific installed Edge153.0.4234.32 at C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe, SHA25681ee5ff42fcec883312170606b10ebbb2b01f5b4cddc2cf485290e40c15b027d, and installed Playwright1.62.1. Verify executable hash before launch. Run the actual changed Vite frontend only at http://127.0.0.1:5175 and an owned real Task API at one ephemeral127.0.0.1 port with that exact Origin; use existing VITE_TASK_API_BASE. All application requests must remain on those loopback endpoints. Use isolated browser profiles, headless by default, no personal profile and disable background networking where supported. At most4 Edge launches, each at most30minutes, and64 PNG screenshots. Actual Git/SQLite/installed-pytest fixtures must cover valid single/team, syntax error, failed assertion, no implementation, zero tests, missing/stale evidence and actual deterministic fixture. Only model execution and binding metadata are disclosed doubles. Verify browser-visible Goal proof and exact Run navigation against HTTP and reopened SQLite identities/digests. Keep recorded-Draft presentation fixtures separate from real remote publication; do not visit external PR links. Inspect desktop/mobile light/dark captures and keyboard interactions. Retain sanitized artifacts under F:/Nerelan-final-audit-evidence-20260911/issue833-browser, use temporary test Git/SQLite/worktrees there, track owned PIDs, and close only owned test browser/server processes gracefully. No broad termination/deletion, providers, credentials, external navigation, installs, WSL/container startup or snapshot update. Any blocking failure or executable/authority mismatch stops this round.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "machine_specific_execution",
        "integration_test",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue833.publish",
      "command": "After all exact-head local and real browser checks pass, push onlycodex/f03-visible-goal-evidence-r3-v1 todddd2024/Nerelan and create exactly one Draft against main@1b87cb41606bfbda0b4b49dd18259550fbf5bb58. One successful push and one successful Draft only; at most3 transport attempts overall, only after readback confirms no mutation. After successful push no further push. Publish disclosed review/evidence and bounded progress comments only to Issue833, its exact Draft,653 and659. Do not mutate other branches/Issues/PRs or repeat completed826 closure.",
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
      "command_id": "issue833.audit",
      "command": "Require all five natural browser_r3 exact-head workflows: CI, Decision Preflight, State Gate, Model Access and Frontend Playwright. Compare actual full diagnostic failed node IDs with accepted locked main; a green nonblocking wrapper is insufficient. Perform a separate disclosed self-audit. No rerun/dispatch or snapshot update. An actual golden failure stops this candidate; preserve exact head/run/actual/expected/diff artifacts for a separately approved successor, never blind refresh or Windows golden substitution.",
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
      "command_id": "issue833.landing",
      "command": "Only after separate disclosed exact-head self-audit, all required natural checks, current unchanged approved Decision/base/head and separately bound immutable landing authority with its own checks, use the existing false/none Owner landing protocol for the exact Issue833 Draft. Require NEW Ready-triggered formal landing-state-gate, existing premerge attestation, live required contexts and immediate main==1b87cb41606bfbda0b4b49dd18259550fbf5bb58, CLEAN/MERGEABLE and no concurrent target mutation. At most one Ready and one ordinary method=merge with expected-head protection; verify actual parents/tree/main and native mainline receipt. No independent human review claim or direct main push.",
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
  ],
  "browser_binding": {
    "execution_surface": "user_local",
    "executable": "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
    "version": "153.0.4234.32",
    "sha256": "81ee5ff42fcec883312170606b10ebbb2b01f5b4cddc2cf485290e40c15b027d",
    "playwright_version": "1.62.1",
    "launch_limit": 4,
    "per_launch_timeout_seconds": 1800,
    "screenshot_limit": 64,
    "frontend_origin": "http://127.0.0.1:5175",
    "api_host": "127.0.0.1",
    "api_port": "ephemeral_owned"
  },
  "run_environment_binding": {
    "run_strategy": "trusted_worker",
    "canonical_repository": "dddd2024/Nerelan",
    "target_owner_branch": "codex/f03-visible-goal-evidence-r3-v1",
    "authority_path": "Path B R3 transition",
    "execution_surfaces": [
      "trusted_worker",
      "user_local",
      "github_control_plane",
      "remote_observation"
    ],
    "legacy_local_surface_forbidden": true
  }
}
```
