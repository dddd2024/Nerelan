# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260912_issue839_visible_goal_evidence_r3_v6",
  "round_id": "round_20260912_issue839_visible_goal_evidence_r3_v6",
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
  "source_issue": 839,
  "parent_issue": 653,
  "repository": "dddd2024/Nerelan",
  "source_issue_body_sha256": "48ad5c1184a7030bd5e5d0b8f5cd760bab20c0670b4649daff572d48b6237e27",
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
  "required_branch": "codex/f03-visible-goal-evidence-r3-v6",
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
    "issue_body_sha256": "48ad5c1184a7030bd5e5d0b8f5cd760bab20c0670b4649daff572d48b6237e27",
    "specification": "CANDIDATE R3 Work Item for remaining F03 visible Goal evidence and actual Edge acceptance. This Issue alone is not execution authority; activate an immutable APPROVED R3 Decision under the user's explicit Owner/self-audit/merge delegation. All such approval/audit/landing actions are disclosed Codex actions, not independent human review.\n\nParent: F03 #653. Locked base: main@1b87cb41606bfbda0b4b49dd18259550fbf5bb58, the ordinary merge of accepted backend Goal proof PR827. Exact branch: codex/f03-visible-goal-evidence-r3-v6. Native mainline receipt is EMITTED/PASSED; main CI34671618527 and State34671618526 succeeded on this base. Actual diagnostic22 failed6327 passed23 skipped1warning has exactly the same22base failure nodes and no new failure. Source826 was completed by Owner with comment5643441247 and closure2026-09-12T04:26:09Z; do not reopen or repeat its closure. No prior branch/history is reused.\n\nThe backend now supplies coherent current task identity, executor provenance, functional proof and bounded publication records for Goal list/detail/page. The UI must make these facts visible and distinguish execution ended, functional verification, pending review, recorded Draft publication and unobserved remote merge/delivery. Goal COMPLETED and Task READY_FOR_REVIEW are not functional verification by themselves.\n\nImplementation contract:\n\n- Reuse the existing PlatformGoal/Run publication types, normalizeFunctionalValidation and FunctionalValidationView. Add the optional Goal proof fields and share a compact presentation label if needed; do not add a second verifier or execution store. A positive badge requires complete current host proof and explicit real-executor provenance. Missing/malformed/stale/failed/zero-test proof must not become verified. Fixture status/provenance must remain visibly distinct even when malformed test input claims real success.\n- GoalProgress shows readable execution/review state and functional status. Detailed checks, actual counts, contract/result digests and exact base/head/tree remain inspectable through the existing proof component. Keep important status visible outside collapsed evidence. Add accessible exact Run links only for materialized task_links; unlaunched plan IDs are not runtime Task IDs. Preserve interrupted recovery controls, dependencies, ordering and progress semantics.\n- Reuse truthful wording from immutable PR819 head477ce00ac161dbc28337b73f646521ff18398be7 where applicable, after checking its actual disposition and the source hunks. Its six paths overlap this scope, but its old Decision/base/history are not authority for this round. Preserve that branch and Draft. Do not hide meaningful status solely to preserve existing screenshots.\n- Home/review Goal COMPLETED labels and derived Roadmap phase/member labels say execution ended/pending acceptance rather than imply functional delivery. Roadmap remains a projection of Goal truth. Recorded publication PENDING/COMMIT_CREATED/PUSHED/COMPLETE/FAILED is separate; COMPLETE means recorded Draft creation, while current remote review/merge is not observed. A recorded PR link is not proof that the remote PR is still Draft or merged.\n- Keep keyboard navigation, mobile wrapping, readable status and existing styles. Correct only the observed reset/focus cascade and Run state/liveness readability defects as specified below; no unrelated redesign, backend change or snapshot replacement. No browser shell/filesystem/credential/policy authority.\n\nExact product allowlist:\n\n```text\nfrontend/src/index.css\nfrontend/src/lib/platform-client.ts\nfrontend/src/lib/functional-validation.ts\nfrontend/src/components/functional-validation.tsx\nfrontend/src/components/goal-progress.tsx\nfrontend/src/routes/home.tsx\nfrontend/src/routes/approvals.tsx\nfrontend/src/routes/roadmap.tsx\nfrontend/src/routes/runs.tsx\nfrontend/tests/platform-home.test.tsx\nfrontend/tests/goal-progress.test.tsx\nfrontend/tests/task-first-lifecycle-states.test.tsx\nfrontend/tests/approvals.test.tsx\nfrontend/tests/roadmap.test.tsx\nfrontend/tests/functional-validation.test.tsx\nfrontend/tests/goal-completion-evidence.test.tsx\nfrontend/e2e/functional-validation.spec.ts\ndocs/functional-validation.md\n```\n\nThe Decision may additionally allow only its immutable project_state/decision_packet.md and the five existing generated gates used by current product rounds. No backend, workflow, dependency/lockfile, schema, validator, database migration or new artifact family is authorized. Preserve existing dirty/stopped worktrees.\n\nRequired deterministic and user-flow acceptance:\n\n1. All existing frontend unit/component tests, npm run lint and production build. Add meaningful Goal rendering/deep-link tests for actual valid/failed/missing/stale/zero/fixture evidence, publication independence, complete/malformed proof, updated server responses and unmaterialized plan rows. Retain existing functional, lifecycle, recovery and accessibility assertions.\n2. Existing backend regressions: tests/platform_v1/test_goal_completion_evidence.py, tests/platform_v1/test_goal_service.py and tests/platform_v1/test_run_read_model.py, plus git diff --check and existing immutable Decision plan/lint/preflight/publication-readiness gates.\n3. Under a separately explicit user_local machine-specific R3 command, run an isolated real Vite frontend and real Task API on loopback, backed by temporary disk SQLite/Git and installed pytest. Seed executions through the existing Goal/test/service seams: valid single and sequential-team, syntax error, failed assertion, no implementation, zero executed tests, missing/stale proof and actual deterministic fixture. Only model execution and binding metadata may be disclosed doubles. Browser-visible Goal proof and exact Run links must agree with actual HTTP and reopened SQLite identities/digests. Confined corruption of a disposable fixture DB may test stale/missing evidence; never alter product runtime state. A synthetic recorded Draft tests presentation only and must not be described as real GitHub publication. Real provider/desktop and #135 publication acceptance remain separate.\n4. Known installed Edge may run only with a temporary profile, headless by default, no personal browser data and loopback-only application requests. Use the installed Playwright1.62.1 library. Read and verify executable provenance before launch; observed candidate is C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe, version153.0.4234.32, SHA25681ee5ff42fcec883312170606b10ebbb2b01f5b4cddc2cf485290e40c15b027d. Current Node path E:/Program Files/nodejs/node.exe and Python C:/Program Files/Python313/python.exe are installed. Existing frontend dependencies resolve through F:/Nerelan-issue799-artifact-handoff-v5/frontend/node_modules to F:/reverse-agent-issue585-desktop0-tauri-r2-v9/frontend/node_modules; verify current manifests/lock compatibility before bounded reuse. A junction to those existing dependencies is permitted only as ignored local tooling; do not install/update packages or stage the junction/cache. No package/browser installation or container/WSL startup. Track owned server/browser PIDs and close only those owned processes after acceptance, without broad termination/deletion.\n5. Capture and inspect desktop/mobile and light/dark browser evidence for the changed Goal flow. This Windows Edge functional/visual inspection does not replace Ubuntu Chromium golden acceptance. Require all naturally triggered exact-head CI, Decision Preflight, State Gate, Model Access and Frontend Playwright checks. Do not rerun/dispatch workflows, weaken assertions or update snapshots in this first round.\n6. If the visible change makes an existing golden fail, preserve the failed head/run and actual/expected/diff artifacts and stop that round. A fresh R3 successor may bind only reviewed exact Ubuntu candidate PNG hashes and affected existing home/settings snapshot paths; no blind refresh or Windows PNG substitution. Do not suppress meaningful UI changes to avoid this acceptance.\n7. Separate disclosed exact-head self-audit, reviewable Draft and existing bounded landing-authority/attestation protocol are required before any Ready/merge. Preserve expected-head ordinary merge protection and immediate no-drift checks. F03 #653 remains open until its complete user-visible acceptance is proved; #659 and the full G0-G6 project goal remain open.\n\nThe fresh Decision must declare browser testing using existing operations machine_specific_execution + integration_test on user_local, with exact loopback bounds and user_local_network_exceptions. browser_execution is not an existing command operation and must not be invented. Set the appropriate browser R3 workflow profile after checking the current schema. Known Edge execution is explicitly granted only by that fresh Decision; current #828 R2 authority does not grant it.\n\nForbidden: provider/model calls, credential/auth-store access, external navigation or publication from the browser, unknown binary execution, dependency installation, snapshots in this round, main push, force push/rebase/squash/amend, automatic merge, tag/release/deploy, runner/workflow dispatch, destructive cleanup, new Gate/receipt/authority store, and any out-of-allowlist product edit. Any blocking check failure or authority/base/head drift stops the round; no fix-forward or silent scope expansion.\n\n\nMachine-specific limits for the fresh Decision: Vite listens only at http://127.0.0.1:5175; the owned Task API binds an ephemeral 127.0.0.1 port and accepts that exact frontend origin. Pass the actual API address through existing VITE_TASK_API_BASE. No browser mock API may substitute for the real acceptance path. Browser application requests are restricted to these owned loopback endpoints; disable background networking where supported and use no personal profile. At most four owned Edge launches, each bounded to30minutes; at most64 PNG screenshots. Owned servers have bounded lifetime and are stopped gracefully; no broad process termination or recursive deletion. Keep isolated profiles/SQLite/Git/worktrees, traces and sanitized evidence under an issue-specific external validation directory. Reobserve Edge SHA256 immediately before launch; mismatch requires renewed explicit authority.\n\nCommit/publication limits: one Decision-only activation before any product change, at most four product commits and two generated-governance commits, one successful initial branch publication and one Draft creation. At most three transport attempts only after readback proves no remote mutation; after successful push no further push under this first round. Validate the exact implementation head before its sole successful publication. No workflow rerun/dispatch. Source/parent/overall progress and a disclosed exact-head self-review may be posted only to this Work Item, its eventual exact Draft, #653 and #659 under the fresh Decision. Do not mutate PR819 or other active work.\n\n\nFresh successor contract: complete the Recent goals execution-label coverage\n\nStopped837 at588626f0511bf2828085497db852f4fef65666c5 passed all434 frontend/114 backend checks, lint/build/diff and nine actual HTTP/Git/SQLite/pytest/Edge cases. All33PNG captures were inspected. Focus indicators, Run label contrast (minimum6.354:1), spacing and mobile lower proof passed, but Home Recent goals still displayed raw COMPLETED for actual fixture and stale-proof Goals. Preserve837 and stopped833/834/835; never retry their helpers or mutate their branches.\n\nRetain all17 frozen Issue838 product files listed below after every SHA256 and unchanged base-blob check, only after this fresh Decision-only activation and PRE_EXECUTION_AUTHORIZED. The same18 product paths remain the allowlist. In home.tsx Recent goals, display the existing goalStatusLabel completion text for COMPLETED; preserve the exact existing display of other lifecycle states, colors, list cap/order and selection behavior. Add meaningful scoped assertions in platform-home.test.tsx for the Recent goals completion text, absence of raw COMPLETED and absence of functional/delivery success wording. Cover the response update and the existing fixture/missing-proof limitations without treating Goal completion as proof. Extend the real browser harness to observe Recent goals in light/dark desktop/mobile and assert the real fixture/stale Goal rows say execution completed/pending review, never raw COMPLETED or functional verified. Scroll those rows into view, capture and restore the selected Goal flow; retain exact navigation and proof identity checks. Add at most four captures under the existing64PNG limit. No new product component, second status store or verifier is authorized.\n\nRetain the universal box-sizing/margin/padding reset in @layer base and the base-layer2px solid existing accent focus-visible outline with2px offset. Retain theme tints plus primary-text styles in Run STATE_STYLES/LIVENESS_STYLES, and preserve all state labels/data/control/API semantics. Keep the existing normalizer/proof component, exact materialized Run links and truthful Goal/approval/Roadmap labels. No unrelated layout/palette/typography/control change.\n\nRepeat all earlier browser checks on this round's exact committed head: nine actual HTTP/Git/SQLite/installed-pytest cases, only model/binding doubles, unchanged actual built-in fixture, SQLite reopen, exact Task title/href/Run navigation, current functional identity/digests and publication disclaimer. Measure48pxdesktop/16pxmobile Home padding and12px task-row vertical padding; exercise Tab/Enter with visible outline/ring, require actual composited Run state/liveness text contrast>=4.5:1 in light/dark, and capture mobile lower result digest/run identity fully within viewport. Preserve no-horizontal-overflow, unlaunched plan rows with no Run link and all desktop/mobile light/dark checks. One new isolated profile; at most4launches,30minutes each,64PNGs. All other installed executable/hash, loopback, owned process, dependency compatibility and zero-provider/credential/install limits above remain binding.\n\nNo previous Decision/gates/history or test result becomes this round's authority/acceptance. Run the full applicable checks again and use a separate disclosed self-review. The empty mobile English composer placeholder wrapping remains an ordinary UX followup outside this scope; it does not authorize GoalComposer changes here.\n\nAll eight existing Ubuntu Chromium home/settings desktop/mobile light/dark goldens may differ because of restored spacing. Every PNG/workflow edit remains forbidden in this first acceptance round. Require all five natural exact-head workflows. A blocking visual mismatch stops the candidate and preserves exact head/run/actual/expected/diff artifacts. Only a fresh separately approved successor may bind reviewed exact Ubuntu PNG hashes for affected existing snapshot paths. No blind refresh, Windows substitution, threshold weakening or CI rerun/dispatch.\n\nFresh v6 successor: await the actual query response notification\n\nIssue838 stopped at activationce1fd821058f971a3707f03fcc748f2ffc8ecbf3 with17 uncommitted product files after1 frontend test failed and434 passed. The new Recent goals response update test asserted before TanStack Query notifyManager delivered its scheduled observer notification; the failure DOM remained RUNNING. No product commit, browser, push or Draft occurred. Preserve838 including its generated gates and test log. Its raw-COMPLETED product fix and existing enhanced color/wording assertions are retained in the frozen files below.\n\nAfter this fresh Decision-only activation and passing gates, reuse only the17 SHA-bound838 product files below. In platform-home.test.tsx, add a bounded existing waitFor around the exact updated fixture-row execution-completed/pending-review label before asserting unchanged order, no raw COMPLETED/functional/delivery success text and actual selection navigation to missing-proof Goal. Preserve all existing assertions and tests. Do not use arbitrary sleeps, change product scheduling, suppress errors, weaken assertions or change any further product behavior. Reuse the prepared but never executed838 real-browser harness with this new round's exact paths/identity and unchanged Recent goals light/dark desktop/mobile assertions. All local checks and the real browser acceptance must run anew on this round; no prior result is acceptance.\n\nThe same18 product paths, browser/hash/loopback/process bounds,64PNG limit, zero-provider/credential/install limits, failure-stop rule, sole push/Draft and separately bound landing requirements remain binding. Ubuntu screenshots may only be reviewed as failed evidence here; no golden updates or reruns. The full F03 and G0-G6 goals remain open.\n\nFrozen product SHA256 values from stopped838:\n\n- docs/functional-validation.md: ec0fba8434547ae1035040641611e2c69578b98e93cfb5a7b654febd5a98abb5\n- frontend/e2e/functional-validation.spec.ts: 2063515e3cb337165bd86920dc162b963226e5aec91be0094958496c79febb21\n- frontend/src/components/functional-validation.tsx: 4dfdd1ed9862b5f8216f2e06bf7f6277d4083a5bec2afffb642b328b0b2fdda1\n- frontend/src/components/goal-progress.tsx: 2372169b966311a79a152243adbd79c12ec83f49264e1616fffbb9b9e20dfcf7\n- frontend/src/index.css: 7e4ffd527ff2eefda593efe52c3ceabe3600941647a192f1f950dbf6b5b5572f\n- frontend/src/lib/functional-validation.ts: dd680cdba3a226cafce340d92a70d8407c0ca755b126f05634be4554e7bb7395\n- frontend/src/lib/platform-client.ts: 4bd42a09223aa199408c2c74b5cdba3494d41ece4139999d04ba913a064c7a55\n- frontend/src/routes/approvals.tsx: 0377b280c8a3263bd026a4ea730ad9397343ecd91b7e4002fb75fbca76222a06\n- frontend/src/routes/home.tsx: c21bf77a762367387ed51b580a184ee02149e50ecad17e9b65f2a9cc2c6df25c\n- frontend/src/routes/roadmap.tsx: 5dc0db058d7c1a94bd40722850602e073d2826d1e10584077f3f03ac605c6099\n- frontend/src/routes/runs.tsx: 2f3ea1113fcca9962b9f8dddb92eb176651d251172b49720af0cd14701d213b6\n- frontend/tests/approvals.test.tsx: aecab5ac6757cd7c759bb0a240b8e327d92604e694195bdfdc4c04c2440fc94b\n- frontend/tests/goal-completion-evidence.test.tsx: 1b174424c602417f1a4b2a8e7f702c37a1c699699389074ae3fbd524dcf8556c\n- frontend/tests/goal-progress.test.tsx: 6d1729b2dd67d40b45f79a630f8a33cb1ed9aa75deb59950095b9fcbd22f4da4\n- frontend/tests/platform-home.test.tsx: 07ebfdfff60caeb856b7a6518369a380d9f674183bc0325ed5ed5ccc8e2c0d05\n- frontend/tests/roadmap.test.tsx: 0e0d55d7c7760d6dc02cfc02f529405735dc13cad63a35a5d02ebd934a27bc8f\n- frontend/tests/task-first-lifecycle-states.test.tsx: cef9302825f9db30926b10ac78bb283446c3f24894c21094790154b46d1c6dd6"
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
    "frontend/src/index.css",
    "frontend/src/lib/platform-client.ts",
    "frontend/src/lib/functional-validation.ts",
    "frontend/src/components/functional-validation.tsx",
    "frontend/src/components/goal-progress.tsx",
    "frontend/src/routes/home.tsx",
    "frontend/src/routes/approvals.tsx",
    "frontend/src/routes/roadmap.tsx",
    "frontend/src/routes/runs.tsx",
    "frontend/tests/platform-home.test.tsx",
    "frontend/tests/goal-progress.test.tsx",
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
    "frontend/src/index.css",
    "frontend/src/lib/platform-client.ts",
    "frontend/src/lib/functional-validation.ts",
    "frontend/src/components/functional-validation.tsx",
    "frontend/src/components/goal-progress.tsx",
    "frontend/src/routes/home.tsx",
    "frontend/src/routes/approvals.tsx",
    "frontend/src/routes/roadmap.tsx",
    "frontend/src/routes/runs.tsx",
    "frontend/tests/platform-home.test.tsx",
    "frontend/tests/goal-progress.test.tsx",
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
      "After all exact-head local and real browser checks pass, push onlycodex/f03-visible-goal-evidence-r3-v6 todddd2024/Nerelan and create exactly one Draft against main@1b87cb41606bfbda0b4b49dd18259550fbf5bb58. One successful push and one successful Draft only; at most3 transport attempts overall, only after readback confirms no mutation. After successful push no further push. Publish disclosed review/evidence and bounded progress comments only to Issue839, its exact Draft,653 and659. Do not mutate other branches/Issues/PRs or repeat completed826 closure.",
      "Only after separate disclosed exact-head self-audit, all required natural checks, current unchanged approved Decision/base/head and separately bound immutable landing authority with its own checks, use the existing false/none Owner landing protocol for the exact Issue839 Draft. Require NEW Ready-triggered formal landing-state-gate, existing premerge attestation, live required contexts and immediate main==1b87cb41606bfbda0b4b49dd18259550fbf5bb58, CLEAN/MERGEABLE and no concurrent target mutation. At most one Ready and one ordinary method=merge with expected-head protection; verify actual parents/tree/main and native mainline receipt. No independent human review claim or direct main push."
    ],
    "user_local_network_exceptions": [
      "On user_local only, use machine-specific installed Edge153.0.4234.32 at C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe, SHA25681ee5ff42fcec883312170606b10ebbb2b01f5b4cddc2cf485290e40c15b027d, and installed Playwright1.62.1. Verify executable hash before launch. Run the actual changed Vite frontend only at http://127.0.0.1:5175 and an owned real Task API at one ephemeral127.0.0.1 port with that exact Origin; use existing VITE_TASK_API_BASE. All application requests must remain on those loopback endpoints. Use isolated browser profiles, headless by default, no personal profile and disable background networking where supported. At most4 Edge launches, each at most30minutes, and64 PNG screenshots. Actual Git/SQLite/installed-pytest fixtures must cover valid single/team, syntax error, failed assertion, no implementation, zero tests, missing/stale evidence and actual deterministic fixture. Only model execution and binding metadata are disclosed doubles. Verify browser-visible Goal proof and exact Run navigation against HTTP and reopened SQLite identities/digests. Keep recorded-Draft presentation fixtures separate from real remote publication; do not visit external PR links. Inspect desktop/mobile light/dark captures and keyboard interactions. Use exact host materialized Task titles in accessible-link expectations. Assert actual48pxdesktop/16pxmobile Home padding and12pxvertical task-row padding, visible focus outlines/rings through Tab/Enter, actual composited Run state/liveness text contrast at least4.5:1 in light/dark themes, and mobile lower evidence digest/run identity scrolled into viewport. Preserve all prior exact identity/proof/navigation and no-horizontal-overflow checks. Retain sanitized artifacts under F:/Nerelan-final-audit-evidence-20260911/issue839-browser, use temporary test Git/SQLite/worktrees there, track owned PIDs, and close only owned test browser/server processes gracefully. No broad termination/deletion, providers, credentials, external navigation, installs, WSL/container startup or snapshot update. Any blocking failure or executable/authority mismatch stops this round. Also inspect the actual Recent goals fixture/stale-proof rows in light/dark desktop/mobile: require execution-ended/pending-review wording, no raw COMPLETED or functional verified wording, unchanged lifecycle semantics and selection. Scroll recent rows into viewport and capture at most4 additional PNGs within the64 total limit; restore the selected Goal flow and retain all prior proof/navigation checks."
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
      "command_id": "issue839.bootstrap",
      "command": "Observe main exactly1b87cb41606bfbda0b4b49dd18259550fbf5bb58, accepted PR827 native receipt/main CI and fresh clean branchcodex/f03-visible-goal-evidence-r3-v6; commit this immutable APPROVED R3 Decision alone as the first activation commit. Run existing startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre and worktree-publication-readiness. Require PRE_EXECUTION_AUTHORIZED and PUBLICATION_READY before product mutation or any browser/server launch. Do not copy prior Decision/gates/history.",
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
      "command_id": "issue839.implement",
      "command": "Implement only the18 product paths in Issue839. After fresh Decision-only activation and passing existing gates, reuse only the17 frozen Issue838 uncommitted product files after exact SHA256 and unchanged base-blob checks. Preserve stopped833/834/835/837/838 and PR819. Retain all frozen Goal proof, exact Run links, truthful Goal/Recent goals/approval/Roadmap labels, publication distinctions, CSS reset/focus and readable Run styles. Correct only the new platform-home test notification timing: use bounded existing waitFor to await the exact updated fixture-row completion label before keeping all list-order, no-raw-COMPLETED/no-functional-success and actual missing-proof Goal selection assertions. No arbitrary sleep, weaker assertion, product scheduler or other runtime behavior change. Reuse the prepared never-executed838 real-browser harness with fresh round paths/identity and retained four-layout Recent goals assertions. No backend/workflow/dependency/schema/validator/snapshot or new component/store/verifier change. Verify installed ignored dependency junction compatibility. All checks must run anew; no previous Decision/gates/history or results confer acceptance.",
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
        "frontend/src/index.css",
        "frontend/src/lib/platform-client.ts",
        "frontend/src/lib/functional-validation.ts",
        "frontend/src/components/functional-validation.tsx",
        "frontend/src/components/goal-progress.tsx",
        "frontend/src/routes/home.tsx",
        "frontend/src/routes/approvals.tsx",
        "frontend/src/routes/roadmap.tsx",
        "frontend/src/routes/runs.tsx",
        "frontend/tests/platform-home.test.tsx",
        "frontend/tests/goal-progress.test.tsx",
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
      "command_id": "issue839.validate",
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
      "command_id": "issue839.browser",
      "command": "On user_local only, use machine-specific installed Edge153.0.4234.32 at C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe, SHA25681ee5ff42fcec883312170606b10ebbb2b01f5b4cddc2cf485290e40c15b027d, and installed Playwright1.62.1. Verify executable hash before launch. Run the actual changed Vite frontend only at http://127.0.0.1:5175 and an owned real Task API at one ephemeral127.0.0.1 port with that exact Origin; use existing VITE_TASK_API_BASE. All application requests must remain on those loopback endpoints. Use isolated browser profiles, headless by default, no personal profile and disable background networking where supported. At most4 Edge launches, each at most30minutes, and64 PNG screenshots. Actual Git/SQLite/installed-pytest fixtures must cover valid single/team, syntax error, failed assertion, no implementation, zero tests, missing/stale evidence and actual deterministic fixture. Only model execution and binding metadata are disclosed doubles. Verify browser-visible Goal proof and exact Run navigation against HTTP and reopened SQLite identities/digests. Keep recorded-Draft presentation fixtures separate from real remote publication; do not visit external PR links. Inspect desktop/mobile light/dark captures and keyboard interactions. Use exact host materialized Task titles in accessible-link expectations. Assert actual48pxdesktop/16pxmobile Home padding and12pxvertical task-row padding, visible focus outlines/rings through Tab/Enter, actual composited Run state/liveness text contrast at least4.5:1 in light/dark themes, and mobile lower evidence digest/run identity scrolled into viewport. Preserve all prior exact identity/proof/navigation and no-horizontal-overflow checks. Retain sanitized artifacts under F:/Nerelan-final-audit-evidence-20260911/issue839-browser, use temporary test Git/SQLite/worktrees there, track owned PIDs, and close only owned test browser/server processes gracefully. No broad termination/deletion, providers, credentials, external navigation, installs, WSL/container startup or snapshot update. Any blocking failure or executable/authority mismatch stops this round. Also inspect the actual Recent goals fixture/stale-proof rows in light/dark desktop/mobile: require execution-ended/pending-review wording, no raw COMPLETED or functional verified wording, unchanged lifecycle semantics and selection. Scroll recent rows into viewport and capture at most4 additional PNGs within the64 total limit; restore the selected Goal flow and retain all prior proof/navigation checks.",
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
      "command_id": "issue839.publish",
      "command": "After all exact-head local and real browser checks pass, push onlycodex/f03-visible-goal-evidence-r3-v6 todddd2024/Nerelan and create exactly one Draft against main@1b87cb41606bfbda0b4b49dd18259550fbf5bb58. One successful push and one successful Draft only; at most3 transport attempts overall, only after readback confirms no mutation. After successful push no further push. Publish disclosed review/evidence and bounded progress comments only to Issue839, its exact Draft,653 and659. Do not mutate other branches/Issues/PRs or repeat completed826 closure.",
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
      "command_id": "issue839.audit",
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
      "command_id": "issue839.landing",
      "command": "Only after separate disclosed exact-head self-audit, all required natural checks, current unchanged approved Decision/base/head and separately bound immutable landing authority with its own checks, use the existing false/none Owner landing protocol for the exact Issue839 Draft. Require NEW Ready-triggered formal landing-state-gate, existing premerge attestation, live required contexts and immediate main==1b87cb41606bfbda0b4b49dd18259550fbf5bb58, CLEAN/MERGEABLE and no concurrent target mutation. At most one Ready and one ordinary method=merge with expected-head protection; verify actual parents/tree/main and native mainline receipt. No independent human review claim or direct main push.",
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
    "target_owner_branch": "codex/f03-visible-goal-evidence-r3-v6",
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
