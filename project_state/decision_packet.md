# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260912_issue844_visible_goal_evidence_r3_v8",
  "round_id": "round_20260912_issue844_visible_goal_evidence_r3_v8",
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
  "decision_scope": "F03_VISIBLE_GOAL_EVIDENCE_FRONTEND_REFINEMENT_REAL_EDGE",
  "source_issue": 844,
  "parent_issue": 653,
  "repository": "dddd2024/Nerelan",
  "source_issue_body_sha256": "1775b98d8629fbef6d46eb321850e3ead69f3f3a2b677359696c0cdd7c5f4e7f",
  "approved_by": "dddd2024 via explicitly delegated Codex owner action",
  "approval_basis": "The user explicitly delegated Owner authority, disclosed self-audit, merge and all tools for project completion, then requested frontend beautification based on the existing style. This is Codex approval, not independent human review.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R2",
  "workflow_profile": "browser_r3",
  "integration_base_ref": "main",
  "base_sha": "1b87cb41606bfbda0b4b49dd18259550fbf5bb58",
  "activation_base_sha": "1b87cb41606bfbda0b4b49dd18259550fbf5bb58",
  "starting_head": "1b87cb41606bfbda0b4b49dd18259550fbf5bb58",
  "required_branch": "codex/f03-visible-goal-evidence-r3-v8",
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
    "issue_body_sha256": "1775b98d8629fbef6d46eb321850e3ead69f3f3a2b677359696c0cdd7c5f4e7f",
    "specification": "## Work Item and delegated Owner approval\n\nRepository: dddd2024/Nerelan\nParent: #653; overall functional acceptance: #659; full G0-G6 goal remains open.\nRisk: R3, Path B. This Issue is a specification; execution requires its fresh immutable APPROVED Decision, generated existing command plan and PRE_EXECUTION_AUTHORIZED.\nOwner: dddd2024 through explicitly delegated Codex action. The user authorized Owner actions, disclosed self-audit and merge for the full project, and now requested: “现在前端还可以在这个风格的基础上美化”. The user also authorized learning from well-designed products. This is not independent human review.\nTarget branch: codex/f03-visible-goal-evidence-r3-v8\nintegration_base_ref: main\nbase_sha: 1b87cb41606bfbda0b4b49dd18259550fbf5bb58\nMaterial scope, Issue body, base or branch change invalidates the snapshot and requires a fresh bounded approval. Preserve every stopped or unrelated worktree and PR.\n\n## Problem and intended result\n\nIssue843 is stopped at 7e8b71a492f23ab65565f850dba8ff44a8616f0a, with no push or Draft. Its exact-head435 frontend tests,114 backend regressions, lint/build and diff check passed. All56 captured Windows PNGs were visually reviewed. Nine real Goal/HTTP/Git/SQLite/installed-pytest cases and Run navigation completed. The final reduced-motion check wrongly required a valid zero-width0% progress fill to be visible. This is an external harness assertion error; whole-browser acceptance was not achieved. All three owned process IDs were observed absent after graceful closure.\n\nPreserve the existing-style frontend refinement and functional evidence implementation byte-for-byte. Reuse only the22 frozen843 product files below after exact SHA256 and unchanged base-blob checks. Do not reuse its Decision/gates/history as authority. Reference principles remain official Linear information hierarchy and Primer form guidance, applied to the existing Nerelan ivory/charcoal/teal style and current React/Tailwind/Lucide components.\n\n## Exact product allowlist\n\n```text\nfrontend/src/index.css\nfrontend/src/lib/platform-client.ts\nfrontend/src/lib/functional-validation.ts\nfrontend/src/components/functional-validation.tsx\nfrontend/src/components/goal-progress.tsx\nfrontend/src/routes/home.tsx\nfrontend/src/routes/approvals.tsx\nfrontend/src/routes/roadmap.tsx\nfrontend/src/routes/runs.tsx\nfrontend/tests/platform-home.test.tsx\nfrontend/tests/goal-progress.test.tsx\nfrontend/tests/task-first-lifecycle-states.test.tsx\nfrontend/tests/approvals.test.tsx\nfrontend/tests/roadmap.test.tsx\nfrontend/tests/functional-validation.test.tsx\nfrontend/tests/goal-completion-evidence.test.tsx\nfrontend/e2e/functional-validation.spec.ts\ndocs/functional-validation.md\nfrontend/src/components/goal-composer.tsx\nfrontend/src/components/goal-current-activity.tsx\nfrontend/src/routes/settings.tsx\nfrontend/src/components/theme-selector.tsx\nfrontend/src/components/connection-binding-editor.tsx\n```\n\nOnly project_state/decision_packet.md and these five existing generated gates may additionally change: command_plan.json, startup_snapshot.json, bootstrap_state.json, transition_command_plan_preview.json, transition_preflight_result.json under project_state/gates/. No new artifact family.\n\n## Implementation contract\n\n1. Materialize exactly the22 SHA-bound843 product files unchanged. Retain all visible Goal proof, fail-closed fixture/provenance normalization, execution/functional/publication distinctions, Run links, truthful Recent/approval/Roadmap labels, responsive composer/progress/activity/settings presentation and keyboard focus. No further product edits, new tests, behavior changes, palette, dependencies, routes or snapshots in this round.\n2. Correct only the new external acceptance harness copy: for an unlaunched Goal, assert the outer progress track is visible and its fill is attached with zero rendered width; assert0/1 task progress. Read computed transition duration from the attached fill under prefers-reduced-motion and require<=0.001 seconds. Do not force positive progress or weaken the motion assertion. Flush presentation metrics after each completed Settings scenario so all four results survive any later failure.\n3. Preserve all843 evidence and stopped worktrees. All acceptance executes anew against this round's exact head. Old passing tests and screenshots are reusable reference evidence only.\n\n## Required acceptance and machine bounds\n\nRun all frontend tests, npm run lint/build, existing114 backend regressions in tests/platform_v1/test_goal_completion_evidence.py, test_goal_service.py and test_run_read_model.py, git diff --check and all existing immutable Decision gates. Retain all meaningful assertions; do not add tests that merely mirror cosmetic classes. All local checks must pass on the exact committed head before publication.\n\nThe fresh R3 Decision may run known installed Edge153.0.4234.32 at C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe, SHA25681ee5ff42fcec883312170606b10ebbb2b01f5b4cddc2cf485290e40c15b027d, through installed Playwright1.62.1. Verify hash before launch. Use user_local machine_specific_execution + integration_test + bounded network_access, never an invented browser_execution operation. Vite only at http://127.0.0.1:5175 and owned Task API at one ephemeral127.0.0.1 port with the exact frontend Origin. At most4 owned Edge launches,30minutes each,64 PNGs, isolated profile and external disposable Git/SQLite/pytest workspaces. Reuse installed Node/Python and the ignored existing frontend dependency junction only after manifest/lock/package integrity compatibility checks; no install/update. Track and gracefully close only owned PIDs.\n\nRepeat the real nine-case Goal/HTTP/Git/SQLite/installed-pytest acceptance and SQLite reopen/exact Run navigation. Only model execution and binding metadata are disclosed doubles; actual builtin deterministic fixture remains unchanged. Synthetic recorded Draft presentation is not remote publication. Inspect light/dark desktop/mobile Goal and Recent flows, keyboard Tab/Enter focus, current proof digests, mobile lower proof and no overflow. Verify Run state/liveness text contrast>=4.5:1. Extend screenshots to polished Home/Settings and mobile input: the empty placeholder and entered multiline text must fit; every field/footer stays reachable by scrolling, settings theme and local form controls work, and keyboard focus remains visible. Settings metadata may use route-confined synthetic responses solely for presentation; explicitly distinguish it from the real Goal API flow. Do not submit credentials, start authentication/probes, or contact providers. Inspect current/empty/loading/error and long-text presentation through the existing fixtures where applicable.\n\nRequire all five naturally triggered exact-head browser_r3 workflows: CI, Decision Preflight, State Gate, Model Access, Frontend Playwright. Compare full diagnostic node IDs to locked main; green nonblocking wrapper is insufficient. Ubuntu and Windows visual acceptance are separate. Any blocking local/browser/CI failure stops the round with no fix-forward. Preserve the exact head/run/artifacts. Snapshot files remain forbidden here. A fresh successor may materialize only individually reviewed final Ubuntu actual PNG hashes to the eight existing home/settings desktop/mobile light/dark paths; no blind refresh, Windows substitution, threshold changes or rerun/dispatch.839 images are pre-polish evidence, not final polished goldens.\n\n## Publication and landing bounds\n\nOne Decision-only activation before product changes; at most4 product and2 generated-governance commits. One successful push to the exact branch and one Draft against main@1b87cb41606bfbda0b4b49dd18259550fbf5bb58; at most3 transport attempts only after readback proves no mutation. No further push after success. Comments limited to this Work Item, its exact Draft,653 and659. Separate disclosed exact-head self-review and fresh separately bound existing landing authority are required before Ready/merge. Use the existing false/none Owner landing protocol, NEW Ready-triggered formal State Gate, existing attestation, current required checks and immediate no-drift/CLEAN/MERGEABLE observation. At most one Ready and one method=merge with expected-head protection; verify parents/tree/main and native mainline receipt. No independent human-review claim.\n\nForbidden: main push, history rewrite/amend, automatic merge, tags/releases/deploy, workflow/runner dispatch or reruns, snapshots in this round, provider/model calls, credential/auth-store access, external browser navigation, unknown binaries, dependency installation, WSL/container startup, destructive cleanup and out-of-allowlist edits. No new Gate, authority store, receipt, verifier or execution runtime.\n\n## Frozen843 product SHA256\n\n- docs/functional-validation.md: ec0fba8434547ae1035040641611e2c69578b98e93cfb5a7b654febd5a98abb5\n- frontend/e2e/functional-validation.spec.ts: 2063515e3cb337165bd86920dc162b963226e5aec91be0094958496c79febb21\n- frontend/src/components/connection-binding-editor.tsx: 111e56bf2e6e7eacf725e6c15eb63f4e40260f0d89de77e3f786917be24f52c4\n- frontend/src/components/functional-validation.tsx: 4dfdd1ed9862b5f8216f2e06bf7f6277d4083a5bec2afffb642b328b0b2fdda1\n- frontend/src/components/goal-composer.tsx: db5c78521ab94a8b94f452c875f21eee3e4f68067dc85379dba98f48e59e186e\n- frontend/src/components/goal-current-activity.tsx: 0a52bb6edae68b1a41fc4ab3922fefc56ef2b45143c4dddd3b2887666bff7b42\n- frontend/src/components/goal-progress.tsx: b7757148d66e0e4fce25f61883b24003acf9c0cb5f5b9d644b7cfdf4d5877601\n- frontend/src/components/theme-selector.tsx: 786d53ccdcae86f0f1ed82226af2035367d179eb0070fffbe2168c9126cd5964\n- frontend/src/index.css: 7e4ffd527ff2eefda593efe52c3ceabe3600941647a192f1f950dbf6b5b5572f\n- frontend/src/lib/functional-validation.ts: dd680cdba3a226cafce340d92a70d8407c0ca755b126f05634be4554e7bb7395\n- frontend/src/lib/platform-client.ts: 4bd42a09223aa199408c2c74b5cdba3494d41ece4139999d04ba913a064c7a55\n- frontend/src/routes/approvals.tsx: 0377b280c8a3263bd026a4ea730ad9397343ecd91b7e4002fb75fbca76222a06\n- frontend/src/routes/home.tsx: 7138be86e5e9ac4e92e133925ddf5421ccdbb79f8277243078f8bd337b638be8\n- frontend/src/routes/roadmap.tsx: 5dc0db058d7c1a94bd40722850602e073d2826d1e10584077f3f03ac605c6099\n- frontend/src/routes/runs.tsx: 2f3ea1113fcca9962b9f8dddb92eb176651d251172b49720af0cd14701d213b6\n- frontend/src/routes/settings.tsx: 62270accedcd6148af4e3004298bb2b7acd1a55cba54b531607dbea5fadf6aec\n- frontend/tests/approvals.test.tsx: aecab5ac6757cd7c759bb0a240b8e327d92604e694195bdfdc4c04c2440fc94b\n- frontend/tests/goal-completion-evidence.test.tsx: 1b174424c602417f1a4b2a8e7f702c37a1c699699389074ae3fbd524dcf8556c\n- frontend/tests/goal-progress.test.tsx: 6d1729b2dd67d40b45f79a630f8a33cb1ed9aa75deb59950095b9fcbd22f4da4\n- frontend/tests/platform-home.test.tsx: 627717c0a6c95a8aa13d4afc91d884b32e1c154f60ac5935c31c8664fb9c41e3\n- frontend/tests/roadmap.test.tsx: 0e0d55d7c7760d6dc02cfc02f529405735dc13cad63a35a5d02ebd934a27bc8f\n- frontend/tests/task-first-lifecycle-states.test.tsx: cef9302825f9db30926b10ac78bb283446c3f24894c21094790154b46d1c6dd6"
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
    "docs/functional-validation.md",
    "frontend/src/components/goal-composer.tsx",
    "frontend/src/components/goal-current-activity.tsx",
    "frontend/src/routes/settings.tsx",
    "frontend/src/components/theme-selector.tsx",
    "frontend/src/components/connection-binding-editor.tsx"
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
    "docs/functional-validation.md",
    "frontend/src/components/goal-composer.tsx",
    "frontend/src/components/goal-current-activity.tsx",
    "frontend/src/routes/settings.tsx",
    "frontend/src/components/theme-selector.tsx",
    "frontend/src/components/connection-binding-editor.tsx"
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
      "After all exact-head local and real browser checks pass, push onlycodex/f03-visible-goal-evidence-r3-v8 todddd2024/Nerelan and create exactly one Draft against main@1b87cb41606bfbda0b4b49dd18259550fbf5bb58. One successful push and one successful Draft only; at most3 transport attempts overall, only after readback confirms no mutation. After successful push no further push. Publish disclosed review/evidence and bounded progress comments only to Issue844, its exact Draft,653 and659. Do not mutate other branches/Issues/PRs or repeat completed826 closure.",
      "Only after separate disclosed exact-head self-audit, all required natural checks, current unchanged approved Decision/base/head and separately bound immutable landing authority with its own checks, use the existing false/none Owner landing protocol for the exact Issue844 Draft. Require NEW Ready-triggered formal landing-state-gate, existing premerge attestation, live required contexts and immediate main==1b87cb41606bfbda0b4b49dd18259550fbf5bb58, CLEAN/MERGEABLE and no concurrent target mutation. At most one Ready and one ordinary method=merge with expected-head protection; verify actual parents/tree/main and native mainline receipt. No independent human review claim or direct main push."
    ],
    "user_local_network_exceptions": [
      "On user_local only, use machine-specific installed Edge153.0.4234.32 at C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe, SHA25681ee5ff42fcec883312170606b10ebbb2b01f5b4cddc2cf485290e40c15b027d, and installed Playwright1.62.1. Verify executable hash before launch. Run the actual changed Vite frontend only at http://127.0.0.1:5175 and an owned real Task API at one ephemeral127.0.0.1 port with that exact Origin; use existing VITE_TASK_API_BASE. All application requests must remain on those loopback endpoints. Use isolated browser profiles, headless by default, no personal profile and disable background networking where supported. At most4 Edge launches, each at most30minutes, and64 PNG screenshots. Actual Git/SQLite/installed-pytest fixtures must cover valid single/team, syntax error, failed assertion, no implementation, zero tests, missing/stale evidence and actual deterministic fixture. Only model execution and binding metadata are disclosed doubles. Verify browser-visible Goal proof and exact Run navigation against HTTP and reopened SQLite identities/digests. Keep recorded-Draft presentation fixtures separate from real remote publication; do not visit external PR links. Inspect desktop/mobile light/dark captures and keyboard interactions. Use exact host materialized Task titles in accessible-link expectations. Assert actual48pxdesktop/16pxmobile Home padding and12pxvertical task-row padding, visible focus outlines/rings through Tab/Enter, actual composited Run state/liveness text contrast at least4.5:1 in light/dark themes, and mobile lower evidence digest/run identity scrolled into viewport. Preserve all prior exact identity/proof/navigation and no-horizontal-overflow checks. Retain sanitized artifacts under F:/Nerelan-final-audit-evidence-20260911/issue844-browser, use temporary test Git/SQLite/worktrees there, track owned PIDs, and close only owned test browser/server processes gracefully. No broad termination/deletion, providers, credentials, external navigation, installs, WSL/container startup or snapshot update. Any blocking failure or executable/authority mismatch stops this round. Also inspect the actual Recent goals fixture/stale-proof rows in light/dark desktop/mobile: require execution-ended/pending-review wording, no raw COMPLETED or functional verified wording, unchanged lifecycle semantics and selection. Scroll recent rows into viewport and capture at most4 additional PNGs within the64 total limit; restore the selected Goal flow and retain all prior proof/navigation checks. Additionally inspect the polished Home and Settings desktop/mobile in both themes, empty mobile placeholder and entered multiline text, long text, empty/loading/error presentation, theme selections, field/footer reachability by scrolling and keyboard focus. Settings metadata may be route-confined synthetic responses only for visual testing, clearly separate from actual nine-case Goal/Task API acceptance. Do not submit credentials, authenticate, save to real model control, invoke probes or contact providers. Remain inside64 total PNGs and all existing launch/loopback bounds. Corrected reduced-motion check must assert visible outer track, attached zero-width fill and0/1 task count, then evaluate computed transition duration<=0.001 seconds. Flush each completed Settings metrics entry immediately. No forced positive progress."
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
      "command_id": "issue844.bootstrap",
      "command": "Observe main exactly1b87cb41606bfbda0b4b49dd18259550fbf5bb58, accepted PR827 native receipt/main CI and fresh clean branchcodex/f03-visible-goal-evidence-r3-v8; commit this immutable APPROVED R3 Decision alone as the first activation commit. Run existing startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre and worktree-publication-readiness. Require PRE_EXECUTION_AUTHORIZED and PUBLICATION_READY before product mutation or any browser/server launch. Do not copy prior Decision/gates/history.",
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
      "command_id": "issue844.implement",
      "command": "Reuse exactly22 frozen Issue843 product files unchanged after full SHA256/base-blob checks and fresh Decision-only activation/PRE_EXECUTION_AUTHORIZED for Issue844. No other product changes. Correct only the external harness: visible outer progress track, attached zero-width fill with0/1 count, computed reduced-motion duration<=0.001s, and metrics flushed after each Settings scenario. Preserve all stopped work. Existing style/reference and functional contracts remain unchanged.",
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
        "docs/functional-validation.md",
        "frontend/src/components/goal-composer.tsx",
        "frontend/src/components/goal-current-activity.tsx",
        "frontend/src/routes/settings.tsx",
        "frontend/src/components/theme-selector.tsx",
        "frontend/src/components/connection-binding-editor.tsx"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "issue844.validate",
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
      "command_id": "issue844.browser",
      "command": "On user_local only, use machine-specific installed Edge153.0.4234.32 at C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe, SHA25681ee5ff42fcec883312170606b10ebbb2b01f5b4cddc2cf485290e40c15b027d, and installed Playwright1.62.1. Verify executable hash before launch. Run the actual changed Vite frontend only at http://127.0.0.1:5175 and an owned real Task API at one ephemeral127.0.0.1 port with that exact Origin; use existing VITE_TASK_API_BASE. All application requests must remain on those loopback endpoints. Use isolated browser profiles, headless by default, no personal profile and disable background networking where supported. At most4 Edge launches, each at most30minutes, and64 PNG screenshots. Actual Git/SQLite/installed-pytest fixtures must cover valid single/team, syntax error, failed assertion, no implementation, zero tests, missing/stale evidence and actual deterministic fixture. Only model execution and binding metadata are disclosed doubles. Verify browser-visible Goal proof and exact Run navigation against HTTP and reopened SQLite identities/digests. Keep recorded-Draft presentation fixtures separate from real remote publication; do not visit external PR links. Inspect desktop/mobile light/dark captures and keyboard interactions. Use exact host materialized Task titles in accessible-link expectations. Assert actual48pxdesktop/16pxmobile Home padding and12pxvertical task-row padding, visible focus outlines/rings through Tab/Enter, actual composited Run state/liveness text contrast at least4.5:1 in light/dark themes, and mobile lower evidence digest/run identity scrolled into viewport. Preserve all prior exact identity/proof/navigation and no-horizontal-overflow checks. Retain sanitized artifacts under F:/Nerelan-final-audit-evidence-20260911/issue844-browser, use temporary test Git/SQLite/worktrees there, track owned PIDs, and close only owned test browser/server processes gracefully. No broad termination/deletion, providers, credentials, external navigation, installs, WSL/container startup or snapshot update. Any blocking failure or executable/authority mismatch stops this round. Also inspect the actual Recent goals fixture/stale-proof rows in light/dark desktop/mobile: require execution-ended/pending-review wording, no raw COMPLETED or functional verified wording, unchanged lifecycle semantics and selection. Scroll recent rows into viewport and capture at most4 additional PNGs within the64 total limit; restore the selected Goal flow and retain all prior proof/navigation checks. Additionally inspect the polished Home and Settings desktop/mobile in both themes, empty mobile placeholder and entered multiline text, long text, empty/loading/error presentation, theme selections, field/footer reachability by scrolling and keyboard focus. Settings metadata may be route-confined synthetic responses only for visual testing, clearly separate from actual nine-case Goal/Task API acceptance. Do not submit credentials, authenticate, save to real model control, invoke probes or contact providers. Remain inside64 total PNGs and all existing launch/loopback bounds. Corrected reduced-motion check must assert visible outer track, attached zero-width fill and0/1 task count, then evaluate computed transition duration<=0.001 seconds. Flush each completed Settings metrics entry immediately. No forced positive progress.",
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
      "command_id": "issue844.publish",
      "command": "After all exact-head local and real browser checks pass, push onlycodex/f03-visible-goal-evidence-r3-v8 todddd2024/Nerelan and create exactly one Draft against main@1b87cb41606bfbda0b4b49dd18259550fbf5bb58. One successful push and one successful Draft only; at most3 transport attempts overall, only after readback confirms no mutation. After successful push no further push. Publish disclosed review/evidence and bounded progress comments only to Issue844, its exact Draft,653 and659. Do not mutate other branches/Issues/PRs or repeat completed826 closure.",
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
      "command_id": "issue844.audit",
      "command": "Require all five natural browser_r3 exact-head workflows: CI, Decision Preflight, State Gate, Model Access and Frontend Playwright. Compare actual full diagnostic failed node IDs with locked main; green nonblocking wrapper is insufficient. Perform a separate disclosed self-audit. No rerun/dispatch or snapshot update. Any golden failure stops this round; preserve exact head/run and all actual/expected/diff artifacts for a fresh reviewed final-PNG hash-bound successor.839 screenshots are pre-polish evidence only, never final goldens.",
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
      "command_id": "issue844.landing",
      "command": "Only after separate disclosed exact-head self-audit, all required natural checks, current unchanged approved Decision/base/head and separately bound immutable landing authority with its own checks, use the existing false/none Owner landing protocol for the exact Issue844 Draft. Require NEW Ready-triggered formal landing-state-gate, existing premerge attestation, live required contexts and immediate main==1b87cb41606bfbda0b4b49dd18259550fbf5bb58, CLEAN/MERGEABLE and no concurrent target mutation. At most one Ready and one ordinary method=merge with expected-head protection; verify actual parents/tree/main and native mainline receipt. No independent human review claim or direct main push.",
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
    "target_owner_branch": "codex/f03-visible-goal-evidence-r3-v8",
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
