# Approved delegated policy phase6 with reference-scope correction

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20261007_issue118_delegated_policy_recovery_r3_v1",
  "round_id": "round_20261007_issue118_delegated_policy_recovery_r3_v1",
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
  "decision_scope": "ISSUE118_FULL_CANONICAL_DELEGATED_POLICY_AND_REAL_PROVIDER_FREE_GOAL",
  "source_issue": 118,
  "parent_issue": 90,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 Owner via approved bounded-controller-delegation; phase selected by delegated Codex controller",
  "approval_basis": "Owner explicitly replied \u6279\u51c6 to exact prospective 12-hour bounded-controller-delegation proposal on2026-10-07; frozen approved proposal SHA256 1285c0b7787ad010cba92f4b31260c138fe138e1d447b8d26a1307a242911b0b. No prior deadline/counter/failure rewritten.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "codex/issue118-delegated-native-recovery-r3-v1-20261007",
  "base_sha": "82c9b185a66561d17cf8a6857cd3add2d23215ca",
  "activation_base_sha": "82c9b185a66561d17cf8a6857cd3add2d23215ca",
  "starting_head": "82c9b185a66561d17cf8a6857cd3add2d23215ca",
  "required_branch": "codex/issue118-delegated-policy-recovery-r3-v1-20261007",
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
  "product_change_commit_limit": 6,
  "generated_governance_commit_limit": 0,
  "normal_push_attempt_limit": 7,
  "draft_pr_creation_limit": 2,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "workflow_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "credential_access_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": false,
  "pull_request_comment_allowed": false,
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
  "local_browser_execution_allowed": true,
  "model_api_invocation_allowed": false,
  "external_reverse_tool_invocation_allowed": false,
  "unknown_binary_execution_allowed": false,
  "destructive_operations_allowed": true,
  "provider_free_acceptance_required": true,
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "semantic_implementation_contract": {
    "specification": "Phase5 Decision-only local activation failed canonical preflight allowed_reference_path_conflict before publication/source/runtime; no Draft/push/source/test/window was performed. Preserve its immutable local branch/commit and blocked report. This phase6 authorized successor uses last verified eligible planning head82c9b185 (Phase4Draft1090), not the ineligible unpublished Phase5 packet. It removes four overlapping read-only references from reference_paths; actual source allowlist, checks, policy/slot/DB, restrictions, budgets and original upperexpiry unchanged. This is the final6/6 upperphase; no further successor phase without new authority.\n\nImplement full canonical PolicyContract validation/storage, trusted non-merge delegated activation, server-derived exact upper authority, durable slot/window and actual provider-free Goal->Task->fixed checker chain. Reuse existing SQLite/Goal/coordinator/private client and mature LocalValidationRunner; no new runtime/state replica/Gate/receipt artifact family. Current renderer local-owner/ACTIVATE/time reset must be removed from production activation flows. Host-only pin configuration verifies immutable git Decision commit+raw digest, current canonical command-plan/preflight/immutability, upper proposal digest, original absolute expiry, slot/DB/host/workspace identities. A raw file verified flag, arbitrary gitHEAD/env SHA or rendererOwner/ACTIVATE cannot grant operation authority; no invented MergeIntent for non-merge policy. Confirmation provenance DELEGATED_CONTROLLER personally_human=false, never personal Owner acceptance. Full policy preserved and hashed with sorted-key UTF8 JSON separators comma/colon, no silent field dropping. Every field/capability explicitly enforced/inactive/unsupported. Selected unavailable editor/network/secrets/privileged adapters fail concretely; no prompt/posthoc checks advertised as OS sandbox. This grant permits only real fixed git_diff_check with pinned paths, model/provider0/GitHubwrite0/publication0. Git internal metadata reads needed for checker are host runtime metadata, never renderer arbitrary file access; use no external diff/textconv/pager/fsmonitor/hooks, no shell interpolation/network/fetch/unknown executables. Path traversal/symlink/workspace/branch/base/upper/digest/capability drift fails closed.\nProduction HTTP activate uses strict server authority path; existing in-process legacy fixtures may remain distinguished, never trusted production legacy windows/bypass. Direct execution/resume/publication and coordinator in configured delegated mode must enforce actual server-resolved task/plan/workspace/window operation. Provider-free Goal plan is existing deterministic planner, explicit validate_task plus frozen validation_command_id; Goal launch evaluates actual capabilities instead of unconditional execute_task. TaskExecution true host checker branch must precede binding/model/router access; use existing Goal configuration category opencode/single with no binding only if supported, while actual run/evidence runtime_kind=host_validation/model_execution_skipped=true; never claim OpenCode/model execution. Preserve durable claim/lease/idempotency/partial effect semantics, receipt capability validate_task not hardcoded execute_task. Complete canonical policy, confirmation, actor, revision/digest, precondition/input/result/budget/evidence bindings persist in existing stores; summary totals SQL over whole window, history bounded stable-snapshot/cursor pagination, >200/>1000 receipts accessible, not larger truncationlimit. Replays preserve spending; insert/finalization failures stop, no reset.\nFrontend gets actual server-owned approved canonical template/digest/delegated provenance, displays actual supported operations/expiry/checker purpose/instance identity. Never silently promise coding/repair when only hygiene checker available. Remove automatic local-owner/ACTIVATE or Date.now expiry grants; retain active window reuse only with exact confirmed identity. Strict nested schema unknownfields rejected, nonnegative budgets only inactive capabilities; enabled publication capability zero necessary quota still rejected. Instance label/identifier must distinguish fresh acceptance DB from historical formal data without exposing raw host paths/secrets; use existing status primitives, no browser filesystem/authority. Historical F:/reverse-agent DB remains untouched/read-only; default configuration may not silently merge/migrate/reset/open it.\nLower allowance:12 source correction rounds,12 optional development invocations,12 mandatory invocations,6 product commits,7 exact branch pushes including activation,2 Draft creation attempts with read-only dedup after ambiguous first failure,8description updates; root alone serializes spending/publication. Full pytest<=2400s, focused<=900s, frontend/native<=900s, static<=120s. Required: relevant authority/Goal/coordinator/store/host tests, frontend typecheck/fullunit tests, fullPlatform excluding same4existing opt-in OpenCode/provider smokes, PathA, diffcheck, canonical gates/current natural exacthead CI originallogs/JUnit, independent exact-head review. Preserve all prior assertions/failures; source-only fixture is not product acceptance.\nOne remaining fresh clone/stack/browser F:/nrl-auth118-owned-policy1, explicit free ports18907Task/18908Model/18909Frontend; original known Node/Edge hashes and valid Microsoft signature; dependency cache metadata/readonly, isolated Vite cache delta only, exact candidate source manifest. Start supported stack once<=180s, no startup retry, one canonical owned cleanup<=120s. Three<=180s native observations: (1) actual home/tasks/settings and small1000x700->max->restore screenshot/client/sidebar geometry, fixed display followsactualclient; (2) exact topfrontend innerWidth/innerHeight smallnormal/max/restored +TaskAPI200 using supported UIA/guarded Unicode input, group repeated accessible wrappers by actual parsed value rather than demand unique UIA nodes; genuine conflicting values fail; native noidentity/noOrigin401/healthready200; (3) actual owned trusted authority policy activation then true Goal create/plan/approve/launch fixed CHECK001 as structured explicit template (UI or actual frontend-frame HTTP through real privatebroker), await original coordinator handle <=30s, record true actual checker/goal/task/receipt/SQLite durable outcome, exhaustedbudget/replay/refusal checks, screenshot real recenttask, then originalownedpageclose/brokerexit/readinessfalse<=25s. All three measured actions share same browser/stack; no appmodel/provider calls or secret/cap values read. Exactly one real activation slot1 charged in cumulative ledger after tests before actual request; secondslot not granted here. Reopen-store/restart persistence tested in isolated fixtures and actual savedSQLite readback; a second full real stack/browser startup/restart is NOT granted in this phase and cannot be claimed. Missing actual restart proof remains explicit. Third observation close+canonicalcleanup required on diagnostic failure. Jobs0/portsclosed/shared metadata afterproof.\nKnown Phase4 original inner-metric observer failed duplicate UIA nodes despite real NORMAL421x608 andTaskHTTP200, no MAX/RESTORED metrics obtained; preserve report/failed flag; actual UI screenshots/client geometry/settingsbottomgap28 passed. Phase3 DraftHTTP499 consumed creation attempt with noPR and no runtime. No pastcounter/deadline reset. Same original upperexpiry; successor only remaining approved aggregate, no automatic infinite renewal. No Ready/merge/main/historyrewrite/tags/release/deploy/package/container/dependencies/.github/workflows/rerun/dispatch/rawcredentials/unknownbinary/sharedruntime/DB cleanup or mutation. No Issue close/fullbacklog/fullPhase118 completion claim. Codex fallback implementation after observed missing trusted authority seam remains explicit; after actual checker success, only that real Goal/Task is attributed to project system.\n\n# Prospective bounded controller delegation \u2014 approval required\n\nThis proposal is not execution authority and does not change any activated Decision, previous expiry, spending, failure or PR acceptance. It addresses repeated permission requests by preauthorizing phase-specific renewal within one finite allowance, rather than resetting counters. Existing Path-B Decision/command-plan/preflight/readiness mechanisms remain mandatory.\n\n## Exact proposed upper scope\n\nRepository: dddd2024/Nerelan only. Goal remains the full project/GitHub backlog; this grant covers the next #118 architecture execution window and its #384 native-client/#811 continuation prerequisites, not completion of the whole backlog.\n\nFirst integration ref: codex/issue118-client-page-close-r3-v1-20261007, exact base874cdfc7848e7ebff22ec2d6bc226cf0fef2e035. A fresh codex/issue118-* branch and immutable Decision-only activation precede each implementation phase and its exact Draft snapshot. Successor phases may use only the exact verified head of the preceding approved planning phase; no implicit main fallback or history rewrite. Current main97d766d7253378c093c31ed29c990cb6921f2ae4 is observed, not a permitted landing target under this proposal.\n\nClock: one12-hour absolute window frozen at the first new activation; all successors retain that same expiry. Expired/terminal prior packets remain unchanged. At window expiry, affected execution stops and evidence/cleanup follow the explicit phase plan; no renewal beyond this upper window.\n\nDelegated approval: within the named scope, the controller may select exact files/checks and approve fresh bounded phase Decisions under this recorded Owner delegation, with transparent approved_by provenance identifying delegated Agent action. That does not constitute personal human review or independent acceptance. No per-step confirmation for already-granted corrections/checks/phase renewal.\n\nSource envelope: existing reverse_agent/platform_v1/**, frontend/src/**, frontend/tests/**, frontend/e2e/**, frontend/trusted-client.mjs, frontend/trusted-client.node-test.mjs, tests/platform_v1/**, relevant existing tests/test_trust_authorization_adapter.py and tests/test_planning_and_github_adapters.py, docs/local-client-session.md, AGENTS.md and docs/agents/governance-reference.md. Each activated phase must enumerate its actual exact file allowlist and forbid unlisted files; the envelope alone is not a staging allowance. Canonical Decision/gate artifacts use the existing mechanisms, with explicit staging grants only for the selected Decision activation; preserve generated gate deltas and unknown/dirty work. No new Gate/verifier/receipt family to manufacture acceptance.\n\n## Work and acceptance\n\n1. Resolve the missing native positive TaskAPI200 evidence on exact existing source. Choose UI controls by actual identity-bound supported patterns; register precise failure step/diagnostic without credentials. Verify foreground identity immediately before any native keyboard use. Capture only owned pixels. Preserve already-proven home/tasks/settings and real page-close lifecycle evidence; no test fixture presented as browser evidence. Source instrumentation, if genuinely required, needs an exact phase source allowlist and focused verification.\n2. Implement full Issue118 Phase A canonical policy/validation, trusted exact-policy Owner confirmation, server-derived upper authority and durable immutable activation. The frontend must not confer authority by filling local-owner/ACTIVATE/verified flags. Reuse applicable existing authority validators through a thin adapter; never invent a merge intent for non-merge activation. Retain mature private transport/SQLite/coordinator boundaries. Each Issue118 canonical field and capability has an explicit enforced/unsupported classification. Unsupported privileged adapters remain unavailable until their own implementation phase; denial alone is not full-product acceptance.\n3. Complete the receipt/morning-summary contract and recovery: totals over the full window, bounded paginated history with stable snapshot/cursor, immutable policy/actor/input/precondition/result/budget/evidence bindings, original spending after restart, durable claims and partial-side-effect reconciliation. More than200 and1000 receipts must not silently change totals or lose accessible history. Reuse the current store and receipt primitives; no second state replica or runtime.\n4. Existing #118 later adapter phases can be designed and implemented provider-free within remaining scope/allowance, with their own exact Decisions/Drafts/tests. Real mark-ready/merge/tag/release/package/container/deployment side effects are outside this grant. No claim that mock adapter tests prove real publication/production operation.\n\nProvider-free mandatory negative acceptance includes Owner/digest/material-edit mismatch, unknown/extra policy fields, repository/branch/path/capability widening, expiry, revision replay, exhausted/corrupted allowance, receipt persistence failure, stale candidate head/check, restart/partial side effect and unsupported capability. Existing checks cannot be weakened. Source fixtures and synthetic Owner/adapter inputs are explicitly distinguished from real runtime acceptance.\n\nRequired phase checks: applicable existing deterministic pytest/frontend/native Node tests, git diff --check, existing transition-preflight PRE_EXECUTION_AUTHORIZED, publication-readiness PUBLICATION_READY, original natural exact-head CI logs/JUnit, independent exact-head review. No repeated passed checks without change/failure/concern; no CI rerun/dispatch. No source change after the exact-head mandatory freeze without a newly counted correction/check cycle. All attempts and failures consume cumulative allowances.\n\nPrefer actual project Goal/Task implementation only when its real trusted authority/runtime can represent the phase and operate within this grant. If it cannot, record the actual capability failure or missing trusted-authority seam, then use Codex. Do not activate an unsafe caller-declared window to make the project appear eligible.\n\n## Additional finite allowances (not resets)\n\nSource corrections24; optional development invocations32; mandatory check invocations36; source/Draft phases6; Decision activations6; product commits12; exact non-main pushes18; new Drafts6; description updates18. Each phase derives smaller limits from the remaining aggregate ledger. Full pytest<=2400s, focused pytest<=900s, frontend/native suite<=900s per invocation; other static/Path-A checks<=120s unless separately enumerated lower bounded command is required. Budget is charged at start, not success.\n\nOwned runtime clones4/stack starts4/browser starts4; total native observation invocations12<=180s each; canonical identity-bound cleanups4<=120s. Each runtime uses a fresh explicitly named F:/nrl-auth118-owned-* directory, explicit free loopback ports, existing dependency cache without install/modification, isolated Vite cache and exact verified source/config manifest. Known executable hashes/Microsoft signature must freshly match; change stops that launch. No repeated launch under a consumed phase slot.\n\nSynthetic/provider-free test windows may be activated only in owned test databases. At most2 real provider-free autonomous-window activations are permitted only after the trusted exact-policy Owner confirmation/upper-authority seam passes its tests and the real policy binds this grant. No live model calls from repository/runtime code or executor/provider dispatch. The repository/runtime model limit remains0; authorized Codex implementation/review agents are distinct from product provider calls.\n\nWith prior recorded totals, maximum cumulative source corrections33 (=9+24), development checks40 (=8+32), owned runtime stack starts8 (=4+4), browsers7 (=3+4), observations18 (=6+12). Previous fixed deadlines and failed records are untouched. New allowance is available only after explicit approval and fresh activation.\n\nParallel work: explicitly permit up to3 subagents for implementation/read-only audit, with one independent exact-head auditor barred from editing the assessed implementation. No agent can approve its own head as independent acceptance. Workers inherit narrower phase scope and remaining allowance, never raw secrets or unrestricted approval authority.\n\n## Forbidden throughout\n\nNo main push, history rewrite, mark-ready/merge/auto-merge, tag/release/publication/deployment, dependency installation/update, workflows/.github mutation, runner/workflow dispatch or rerun, cross-repository writes, raw credentials/secrets, model/provider calls, unknown/hostile binary execution, broad cleanup/delete/reset/stash/restore/bulk-stage, or touching an unrelated active owner's task/runtime. Existing GitHub CLI may perform scoped repository observation and exact non-main push/Draft/description operations only; no raw credential access or new credential store.\n\nAny unavailable mandatory check, mandatory failure, scope/identity drift, unknown sensitive delta, exhausted allowance or expiry stops the affected operation. Preauthorized successors may handle in-scope product/infrastructure failures only with fresh immutable authority, same upper absolute expiry and remaining cumulative allowance; no reset. Do not represent Draft/CI/self-review as landing or full Issue118/full-goal completion.\n\nFROZEN_UPPER_EXPIRES=2026-10-07T22:31:23.893263+00:00",
    "completion_boundary": "Canonical delegated policy +one actual hygiene-check Goal/Task +fullstore receipt/history/persistence checks +actual native viewport proof. No arbitrary editing sandbox/provider/GitHubprivilege/landing/fullbacklog acceptance."
  },
  "bootstrap_exception_files": [
    "project_state/decision_packet.md"
  ],
  "bootstrap_exception_commands": [],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/platform_v1/authority_adapter.py",
    "reverse_agent/platform_v1/autonomy.py",
    "reverse_agent/platform_v1/control_store.py",
    "reverse_agent/platform_v1/trusted_host.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/goal_service.py",
    "reverse_agent/platform_v1/unattended_coordinator.py",
    "reverse_agent/platform_v1/task_execution.py",
    "reverse_agent/platform_v1/task_runtime.py",
    "reverse_agent/platform_v1/publication_controller.py",
    "frontend/src/types/index.ts",
    "frontend/src/schemas/policy.ts",
    "frontend/src/lib/policy-serializer.ts",
    "frontend/src/lib/platform-client.ts",
    "frontend/src/lib/goal-start-operation.ts",
    "frontend/src/lib/goal-continuation-operation.ts",
    "frontend/src/components/goal-composer.tsx",
    "frontend/src/components/autonomous-window-editor.tsx",
    "frontend/src/components/custom-policy-editor.tsx",
    "frontend/src/components/sidebar.tsx",
    "frontend/src/hooks/use-platform.ts",
    "docs/local-client-session.md",
    "tests/platform_v1/test_autonomy.py",
    "tests/platform_v1/test_autonomy_window_lifecycle.py",
    "tests/platform_v1/test_trusted_host.py",
    "tests/platform_v1/test_task_service.py",
    "tests/platform_v1/test_goal_service.py",
    "tests/platform_v1/test_unattended_coordinator.py",
    "tests/platform_v1/test_task_runtime.py",
    "tests/platform_v1/test_goal_configuration.py",
    "tests/platform_v1/test_goal_functional_checks.py",
    "tests/platform_v1/test_publication_controller.py",
    "tests/platform_v1/test_repository_workspace.py",
    "tests/platform_v1/test_run_read_model.py",
    "tests/platform_v1/test_task_client_auth.py",
    "tests/platform_v1/test_unattended_coordinator_shutdown.py",
    "tests/test_trust_authorization_adapter.py",
    "tests/test_planning_and_github_adapters.py",
    "frontend/tests/policy-validation.test.ts",
    "frontend/tests/policy-serialization.test.ts",
    "frontend/tests/goal-start-recovery.test.ts",
    "frontend/tests/goal-continuation-activation-errors.test.ts",
    "frontend/tests/compact-goal-composer.test.tsx",
    "frontend/tests/approvals.test.tsx",
    "frontend/tests/task-first-sidebar.test.tsx"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/platform_v1/authority_adapter.py",
    "reverse_agent/platform_v1/autonomy.py",
    "reverse_agent/platform_v1/control_store.py",
    "reverse_agent/platform_v1/trusted_host.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/goal_service.py",
    "reverse_agent/platform_v1/unattended_coordinator.py",
    "reverse_agent/platform_v1/task_execution.py",
    "reverse_agent/platform_v1/task_runtime.py",
    "reverse_agent/platform_v1/publication_controller.py",
    "frontend/src/types/index.ts",
    "frontend/src/schemas/policy.ts",
    "frontend/src/lib/policy-serializer.ts",
    "frontend/src/lib/platform-client.ts",
    "frontend/src/lib/goal-start-operation.ts",
    "frontend/src/lib/goal-continuation-operation.ts",
    "frontend/src/components/goal-composer.tsx",
    "frontend/src/components/autonomous-window-editor.tsx",
    "frontend/src/components/custom-policy-editor.tsx",
    "frontend/src/components/sidebar.tsx",
    "frontend/src/hooks/use-platform.ts",
    "docs/local-client-session.md",
    "tests/platform_v1/test_autonomy.py",
    "tests/platform_v1/test_autonomy_window_lifecycle.py",
    "tests/platform_v1/test_trusted_host.py",
    "tests/platform_v1/test_task_service.py",
    "tests/platform_v1/test_goal_service.py",
    "tests/platform_v1/test_unattended_coordinator.py",
    "tests/platform_v1/test_task_runtime.py",
    "tests/platform_v1/test_goal_configuration.py",
    "tests/platform_v1/test_goal_functional_checks.py",
    "tests/platform_v1/test_publication_controller.py",
    "tests/platform_v1/test_repository_workspace.py",
    "tests/platform_v1/test_run_read_model.py",
    "tests/platform_v1/test_task_client_auth.py",
    "tests/platform_v1/test_unattended_coordinator_shutdown.py",
    "tests/test_trust_authorization_adapter.py",
    "tests/test_planning_and_github_adapters.py",
    "frontend/tests/policy-validation.test.ts",
    "frontend/tests/policy-serialization.test.ts",
    "frontend/tests/goal-start-recovery.test.ts",
    "frontend/tests/goal-continuation-activation-errors.test.ts",
    "frontend/tests/compact-goal-composer.test.tsx",
    "frontend/tests/approvals.test.tsx",
    "frontend/tests/task-first-sidebar.test.tsx"
  ],
  "generated_artifact_paths": [
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "AGENTS.md",
    "docs/agents/governance-reference.md",
    ".codex-skills/reverse-agent-iteration/SKILL.md",
    "reverse_agent/platform_v1/local_client_session.py",
    "reverse_agent/platform_v1/run_store.py",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/model_access/service.py",
    ".github/workflows/ci.yml",
    "frontend/src/lib/task-client.ts",
    "frontend/src/lib/repository-client.ts"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md",
    ".github/**",
    ".codex-skills/**",
    "dev-up.ps1",
    "dev-down.ps1",
    "pyproject.toml",
    "project_state/rounds/**",
    "project_state/mainline_merge_intents/**",
    "**/secrets/**",
    "**/.env",
    "**/auth.json"
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
    "unknown_binary_execution",
    "external_reverse_tool_invocation",
    "tag_or_release",
    "dependency_install",
    "generated_governance_commit",
    "raw_secret_read_or_export",
    "model_provider_config_mutation",
    "payment",
    "process_stop_without_identity",
    "issue_comment",
    "pull_request_comment",
    "raw_credential_read_copy_or_print",
    "automatic_GPT_fallback_or_retries",
    "shared_dependency_mutation",
    "existing_model_configuration_mutation",
    "unknown_process_stop",
    "ignore_rules_or_sandbox_bypass",
    "existing_runtime_or_configuration_mutation",
    "application_model_retry",
    "model_fallback",
    "raw_managed_session_access",
    "existing_task_or_runtime_mutation",
    "destructive_outside_new_owned_disposable_fixture_process_groups_or_scratch",
    "self_independent_acceptance"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "workflow_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": true,
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
    "user_local_network_exceptions": [
      "Only owned18907Task/18908Model/18909Frontend/ephemeralrelay and provider-free test fixture loopbacks; fixedchecker no network; model/provider/authprobe0."
    ],
    "github_control_plane_network_exceptions": [
      "<=7exactpushescodex/issue118-delegated-policy-recovery-r3-v1-20261007, <=2Draftattempts with dedup againstcodex/issue118-delegated-native-recovery-r3-v1-20261007@82c9b185a66561d17cf8a6857cd3add2d23215ca, <=8descriptions, scopedoriginalCIreads; nootherwrites."
    ]
  },
  "path_risk_floor": [
    {
      "pattern": "project_state/**",
      "minimum_risk": "R2"
    },
    {
      "pattern": "reverse_agent/platform_v1/functional_validation.py",
      "minimum_risk": "R2"
    }
  ],
  "allowed_commands": [
    {
      "command_id": "native.bootstrap",
      "command": "Fresh bounded Decision-only activation and canonical gates",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "commit",
        "local_static_check",
        "command_plan_generation",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "project_state/decision_packet.md"
      ],
      "produced_artifacts": [
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "native.implementation",
      "command": "Phase5 Decision-only local activation failed canonical preflight allowed_reference_path_conflict before publication/source/runtime; no Draft/push/source/test/window was performed. Preserve its immutable local branch/commit and blocked report. This phase6 authorized successor uses last verified eligible planning head82c9b185 (Phase4Draft1090), not the ineligible unpublished Phase5 packet. It removes four overlapping read-only references from reference_paths; actual source allowlist, checks, policy/slot/DB, restrictions, budgets and original upperexpiry unchanged. This is the final6/6 upperphase; no further successor phase without new authority.\n\nImplement full canonical PolicyContract validation/storage, trusted non-merge delegated activation, server-derived exact upper authority, durable slot/window and actual provider-free Goal->Task->fixed checker chain. Reuse existing SQLite/Goal/coordinator/private client and mature LocalValidationRunner; no new runtime/state replica/Gate/receipt artifact family. Current renderer local-owner/ACTIVATE/time reset must be removed from production activation flows. Host-only pin configuration verifies immutable git Decision commit+raw digest, current canonical command-plan/preflight/immutability, upper proposal digest, original absolute expiry, slot/DB/host/workspace identities. A raw file verified flag, arbitrary gitHEAD/env SHA or rendererOwner/ACTIVATE cannot grant operation authority; no invented MergeIntent for non-merge policy. Confirmation provenance DELEGATED_CONTROLLER personally_human=false, never personal Owner acceptance. Full policy preserved and hashed with sorted-key UTF8 JSON separators comma/colon, no silent field dropping. Every field/capability explicitly enforced/inactive/unsupported. Selected unavailable editor/network/secrets/privileged adapters fail concretely; no prompt/posthoc checks advertised as OS sandbox. This grant permits only real fixed git_diff_check with pinned paths, model/provider0/GitHubwrite0/publication0. Git internal metadata reads needed for checker are host runtime metadata, never renderer arbitrary file access; use no external diff/textconv/pager/fsmonitor/hooks, no shell interpolation/network/fetch/unknown executables. Path traversal/symlink/workspace/branch/base/upper/digest/capability drift fails closed.\nProduction HTTP activate uses strict server authority path; existing in-process legacy fixtures may remain distinguished, never trusted production legacy windows/bypass. Direct execution/resume/publication and coordinator in configured delegated mode must enforce actual server-resolved task/plan/workspace/window operation. Provider-free Goal plan is existing deterministic planner, explicit validate_task plus frozen validation_command_id; Goal launch evaluates actual capabilities instead of unconditional execute_task. TaskExecution true host checker branch must precede binding/model/router access; use existing Goal configuration category opencode/single with no binding only if supported, while actual run/evidence runtime_kind=host_validation/model_execution_skipped=true; never claim OpenCode/model execution. Preserve durable claim/lease/idempotency/partial effect semantics, receipt capability validate_task not hardcoded execute_task. Complete canonical policy, confirmation, actor, revision/digest, precondition/input/result/budget/evidence bindings persist in existing stores; summary totals SQL over whole window, history bounded stable-snapshot/cursor pagination, >200/>1000 receipts accessible, not larger truncationlimit. Replays preserve spending; insert/finalization failures stop, no reset.\nFrontend gets actual server-owned approved canonical template/digest/delegated provenance, displays actual supported operations/expiry/checker purpose/instance identity. Never silently promise coding/repair when only hygiene checker available. Remove automatic local-owner/ACTIVATE or Date.now expiry grants; retain active window reuse only with exact confirmed identity. Strict nested schema unknownfields rejected, nonnegative budgets only inactive capabilities; enabled publication capability zero necessary quota still rejected. Instance label/identifier must distinguish fresh acceptance DB from historical formal data without exposing raw host paths/secrets; use existing status primitives, no browser filesystem/authority. Historical F:/reverse-agent DB remains untouched/read-only; default configuration may not silently merge/migrate/reset/open it.\nLower allowance:12 source correction rounds,12 optional development invocations,12 mandatory invocations,6 product commits,7 exact branch pushes including activation,2 Draft creation attempts with read-only dedup after ambiguous first failure,8description updates; root alone serializes spending/publication. Full pytest<=2400s, focused<=900s, frontend/native<=900s, static<=120s. Required: relevant authority/Goal/coordinator/store/host tests, frontend typecheck/fullunit tests, fullPlatform excluding same4existing opt-in OpenCode/provider smokes, PathA, diffcheck, canonical gates/current natural exacthead CI originallogs/JUnit, independent exact-head review. Preserve all prior assertions/failures; source-only fixture is not product acceptance.\nOne remaining fresh clone/stack/browser F:/nrl-auth118-owned-policy1, explicit free ports18907Task/18908Model/18909Frontend; original known Node/Edge hashes and valid Microsoft signature; dependency cache metadata/readonly, isolated Vite cache delta only, exact candidate source manifest. Start supported stack once<=180s, no startup retry, one canonical owned cleanup<=120s. Three<=180s native observations: (1) actual home/tasks/settings and small1000x700->max->restore screenshot/client/sidebar geometry, fixed display followsactualclient; (2) exact topfrontend innerWidth/innerHeight smallnormal/max/restored +TaskAPI200 using supported UIA/guarded Unicode input, group repeated accessible wrappers by actual parsed value rather than demand unique UIA nodes; genuine conflicting values fail; native noidentity/noOrigin401/healthready200; (3) actual owned trusted authority policy activation then true Goal create/plan/approve/launch fixed CHECK001 as structured explicit template (UI or actual frontend-frame HTTP through real privatebroker), await original coordinator handle <=30s, record true actual checker/goal/task/receipt/SQLite durable outcome, exhaustedbudget/replay/refusal checks, screenshot real recenttask, then originalownedpageclose/brokerexit/readinessfalse<=25s. All three measured actions share same browser/stack; no appmodel/provider calls or secret/cap values read. Exactly one real activation slot1 charged in cumulative ledger after tests before actual request; secondslot not granted here. Reopen-store/restart persistence tested in isolated fixtures and actual savedSQLite readback; a second full real stack/browser startup/restart is NOT granted in this phase and cannot be claimed. Missing actual restart proof remains explicit. Third observation close+canonicalcleanup required on diagnostic failure. Jobs0/portsclosed/shared metadata afterproof.\nKnown Phase4 original inner-metric observer failed duplicate UIA nodes despite real NORMAL421x608 andTaskHTTP200, no MAX/RESTORED metrics obtained; preserve report/failed flag; actual UI screenshots/client geometry/settingsbottomgap28 passed. Phase3 DraftHTTP499 consumed creation attempt with noPR and no runtime. No pastcounter/deadline reset. Same original upperexpiry; successor only remaining approved aggregate, no automatic infinite renewal. No Ready/merge/main/historyrewrite/tags/release/deploy/package/container/dependencies/.github/workflows/rerun/dispatch/rawcredentials/unknownbinary/sharedruntime/DB cleanup or mutation. No Issue close/fullbacklog/fullPhase118 completion claim. Codex fallback implementation after observed missing trusted authority seam remains explicit; after actual checker success, only that real Goal/Task is attributed to project system.\n\n# Prospective bounded controller delegation \u2014 approval required\n\nThis proposal is not execution authority and does not change any activated Decision, previous expiry, spending, failure or PR acceptance. It addresses repeated permission requests by preauthorizing phase-specific renewal within one finite allowance, rather than resetting counters. Existing Path-B Decision/command-plan/preflight/readiness mechanisms remain mandatory.\n\n## Exact proposed upper scope\n\nRepository: dddd2024/Nerelan only. Goal remains the full project/GitHub backlog; this grant covers the next #118 architecture execution window and its #384 native-client/#811 continuation prerequisites, not completion of the whole backlog.\n\nFirst integration ref: codex/issue118-client-page-close-r3-v1-20261007, exact base874cdfc7848e7ebff22ec2d6bc226cf0fef2e035. A fresh codex/issue118-* branch and immutable Decision-only activation precede each implementation phase and its exact Draft snapshot. Successor phases may use only the exact verified head of the preceding approved planning phase; no implicit main fallback or history rewrite. Current main97d766d7253378c093c31ed29c990cb6921f2ae4 is observed, not a permitted landing target under this proposal.\n\nClock: one12-hour absolute window frozen at the first new activation; all successors retain that same expiry. Expired/terminal prior packets remain unchanged. At window expiry, affected execution stops and evidence/cleanup follow the explicit phase plan; no renewal beyond this upper window.\n\nDelegated approval: within the named scope, the controller may select exact files/checks and approve fresh bounded phase Decisions under this recorded Owner delegation, with transparent approved_by provenance identifying delegated Agent action. That does not constitute personal human review or independent acceptance. No per-step confirmation for already-granted corrections/checks/phase renewal.\n\nSource envelope: existing reverse_agent/platform_v1/**, frontend/src/**, frontend/tests/**, frontend/e2e/**, frontend/trusted-client.mjs, frontend/trusted-client.node-test.mjs, tests/platform_v1/**, relevant existing tests/test_trust_authorization_adapter.py and tests/test_planning_and_github_adapters.py, docs/local-client-session.md, AGENTS.md and docs/agents/governance-reference.md. Each activated phase must enumerate its actual exact file allowlist and forbid unlisted files; the envelope alone is not a staging allowance. Canonical Decision/gate artifacts use the existing mechanisms, with explicit staging grants only for the selected Decision activation; preserve generated gate deltas and unknown/dirty work. No new Gate/verifier/receipt family to manufacture acceptance.\n\n## Work and acceptance\n\n1. Resolve the missing native positive TaskAPI200 evidence on exact existing source. Choose UI controls by actual identity-bound supported patterns; register precise failure step/diagnostic without credentials. Verify foreground identity immediately before any native keyboard use. Capture only owned pixels. Preserve already-proven home/tasks/settings and real page-close lifecycle evidence; no test fixture presented as browser evidence. Source instrumentation, if genuinely required, needs an exact phase source allowlist and focused verification.\n2. Implement full Issue118 Phase A canonical policy/validation, trusted exact-policy Owner confirmation, server-derived upper authority and durable immutable activation. The frontend must not confer authority by filling local-owner/ACTIVATE/verified flags. Reuse applicable existing authority validators through a thin adapter; never invent a merge intent for non-merge activation. Retain mature private transport/SQLite/coordinator boundaries. Each Issue118 canonical field and capability has an explicit enforced/unsupported classification. Unsupported privileged adapters remain unavailable until their own implementation phase; denial alone is not full-product acceptance.\n3. Complete the receipt/morning-summary contract and recovery: totals over the full window, bounded paginated history with stable snapshot/cursor, immutable policy/actor/input/precondition/result/budget/evidence bindings, original spending after restart, durable claims and partial-side-effect reconciliation. More than200 and1000 receipts must not silently change totals or lose accessible history. Reuse the current store and receipt primitives; no second state replica or runtime.\n4. Existing #118 later adapter phases can be designed and implemented provider-free within remaining scope/allowance, with their own exact Decisions/Drafts/tests. Real mark-ready/merge/tag/release/package/container/deployment side effects are outside this grant. No claim that mock adapter tests prove real publication/production operation.\n\nProvider-free mandatory negative acceptance includes Owner/digest/material-edit mismatch, unknown/extra policy fields, repository/branch/path/capability widening, expiry, revision replay, exhausted/corrupted allowance, receipt persistence failure, stale candidate head/check, restart/partial side effect and unsupported capability. Existing checks cannot be weakened. Source fixtures and synthetic Owner/adapter inputs are explicitly distinguished from real runtime acceptance.\n\nRequired phase checks: applicable existing deterministic pytest/frontend/native Node tests, git diff --check, existing transition-preflight PRE_EXECUTION_AUTHORIZED, publication-readiness PUBLICATION_READY, original natural exact-head CI logs/JUnit, independent exact-head review. No repeated passed checks without change/failure/concern; no CI rerun/dispatch. No source change after the exact-head mandatory freeze without a newly counted correction/check cycle. All attempts and failures consume cumulative allowances.\n\nPrefer actual project Goal/Task implementation only when its real trusted authority/runtime can represent the phase and operate within this grant. If it cannot, record the actual capability failure or missing trusted-authority seam, then use Codex. Do not activate an unsafe caller-declared window to make the project appear eligible.\n\n## Additional finite allowances (not resets)\n\nSource corrections24; optional development invocations32; mandatory check invocations36; source/Draft phases6; Decision activations6; product commits12; exact non-main pushes18; new Drafts6; description updates18. Each phase derives smaller limits from the remaining aggregate ledger. Full pytest<=2400s, focused pytest<=900s, frontend/native suite<=900s per invocation; other static/Path-A checks<=120s unless separately enumerated lower bounded command is required. Budget is charged at start, not success.\n\nOwned runtime clones4/stack starts4/browser starts4; total native observation invocations12<=180s each; canonical identity-bound cleanups4<=120s. Each runtime uses a fresh explicitly named F:/nrl-auth118-owned-* directory, explicit free loopback ports, existing dependency cache without install/modification, isolated Vite cache and exact verified source/config manifest. Known executable hashes/Microsoft signature must freshly match; change stops that launch. No repeated launch under a consumed phase slot.\n\nSynthetic/provider-free test windows may be activated only in owned test databases. At most2 real provider-free autonomous-window activations are permitted only after the trusted exact-policy Owner confirmation/upper-authority seam passes its tests and the real policy binds this grant. No live model calls from repository/runtime code or executor/provider dispatch. The repository/runtime model limit remains0; authorized Codex implementation/review agents are distinct from product provider calls.\n\nWith prior recorded totals, maximum cumulative source corrections33 (=9+24), development checks40 (=8+32), owned runtime stack starts8 (=4+4), browsers7 (=3+4), observations18 (=6+12). Previous fixed deadlines and failed records are untouched. New allowance is available only after explicit approval and fresh activation.\n\nParallel work: explicitly permit up to3 subagents for implementation/read-only audit, with one independent exact-head auditor barred from editing the assessed implementation. No agent can approve its own head as independent acceptance. Workers inherit narrower phase scope and remaining allowance, never raw secrets or unrestricted approval authority.\n\n## Forbidden throughout\n\nNo main push, history rewrite, mark-ready/merge/auto-merge, tag/release/publication/deployment, dependency installation/update, workflows/.github mutation, runner/workflow dispatch or rerun, cross-repository writes, raw credentials/secrets, model/provider calls, unknown/hostile binary execution, broad cleanup/delete/reset/stash/restore/bulk-stage, or touching an unrelated active owner's task/runtime. Existing GitHub CLI may perform scoped repository observation and exact non-main push/Draft/description operations only; no raw credential access or new credential store.\n\nAny unavailable mandatory check, mandatory failure, scope/identity drift, unknown sensitive delta, exhausted allowance or expiry stops the affected operation. Preauthorized successors may handle in-scope product/infrastructure failures only with fresh immutable authority, same upper absolute expiry and remaining cumulative allowance; no reset. Do not represent Draft/CI/self-review as landing or full Issue118/full-goal completion.\n\nFROZEN_UPPER_EXPIRES=2026-10-07T22:31:23.893263+00:00",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "integration_test",
        "local_static_check",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/platform_v1/authority_adapter.py",
        "reverse_agent/platform_v1/autonomy.py",
        "reverse_agent/platform_v1/control_store.py",
        "reverse_agent/platform_v1/trusted_host.py",
        "reverse_agent/platform_v1/task_service.py",
        "reverse_agent/platform_v1/goal_service.py",
        "reverse_agent/platform_v1/unattended_coordinator.py",
        "reverse_agent/platform_v1/task_execution.py",
        "reverse_agent/platform_v1/task_runtime.py",
        "reverse_agent/platform_v1/publication_controller.py",
        "frontend/src/types/index.ts",
        "frontend/src/schemas/policy.ts",
        "frontend/src/lib/policy-serializer.ts",
        "frontend/src/lib/platform-client.ts",
        "frontend/src/lib/goal-start-operation.ts",
        "frontend/src/lib/goal-continuation-operation.ts",
        "frontend/src/components/goal-composer.tsx",
        "frontend/src/components/autonomous-window-editor.tsx",
        "frontend/src/components/custom-policy-editor.tsx",
        "frontend/src/components/sidebar.tsx",
        "frontend/src/hooks/use-platform.ts",
        "docs/local-client-session.md",
        "tests/platform_v1/test_autonomy.py",
        "tests/platform_v1/test_autonomy_window_lifecycle.py",
        "tests/platform_v1/test_trusted_host.py",
        "tests/platform_v1/test_task_service.py",
        "tests/platform_v1/test_goal_service.py",
        "tests/platform_v1/test_unattended_coordinator.py",
        "tests/platform_v1/test_task_runtime.py",
        "tests/platform_v1/test_goal_configuration.py",
        "tests/platform_v1/test_goal_functional_checks.py",
        "tests/platform_v1/test_publication_controller.py",
        "tests/platform_v1/test_repository_workspace.py",
        "tests/platform_v1/test_run_read_model.py",
        "tests/platform_v1/test_task_client_auth.py",
        "tests/platform_v1/test_unattended_coordinator_shutdown.py",
        "tests/test_trust_authorization_adapter.py",
        "tests/test_planning_and_github_adapters.py",
        "frontend/tests/policy-validation.test.ts",
        "frontend/tests/policy-serialization.test.ts",
        "frontend/tests/goal-start-recovery.test.ts",
        "frontend/tests/goal-continuation-activation-errors.test.ts",
        "frontend/tests/compact-goal-composer.test.tsx",
        "frontend/tests/approvals.test.tsx",
        "frontend/tests/task-first-sidebar.test.tsx"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "native.validation",
      "command": "Current applicable pytest, frontend typecheck/fullunits, focusedNode, fullPlatform4originaloptinsdeselected, PathA/diff/currentcanonicalgates; actual owned native realGoal/window/checker acceptance per specification.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "integration_test",
        "diff_validation",
        "local_static_check",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "native.publication",
      "command": "<=7exactpushescodex/issue118-delegated-policy-recovery-r3-v1-20261007, <=2Draftattempts/dedup againstcodex/issue118-delegated-native-recovery-r3-v1-20261007@82c9b185a66561d17cf8a6857cd3add2d23215ca, <=8descriptions, originalCIscopedreadonly.",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "github_control_plane",
      "operations": [
        "push",
        "draft_pr",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "issue_completion_close_allowed": [],
  "runtime_scratch_policy": {
    "paths": [],
    "stage_allowed": false,
    "note": "Only fresh owned F:/nrl-auth118-owned-policy1; exact candidate source plus isolatedVitecache override; no historical DB/runtime writes."
  },
  "workstream_id": "issue118-delegation-phase6-policy-recovery-20261007",
  "source_issues": [
    118,
    384
  ],
  "local_browser_launch_limit": 1,
  "execution_window_hours": 12,
  "integration_observation_surface": "user_local_exact_planning_base_fresh_branch",
  "runtime_host_launch_limit": 1,
  "frontend_launch_limit": 1,
  "approval_event_or_time": "2026-10-07T10:31:23.893263+00:00",
  "credential_status_probe_limit": 0,
  "provider_network_call_limit": 0,
  "pull_request_description_update_limit": 8,
  "runtime_acceptance_limits": {
    "clone": 1,
    "stack_start": 1,
    "browser_start": 1,
    "observations": 3,
    "normal_cleanup": 1,
    "source_corrections": 12,
    "source_checks_replay": 0,
    "prior_runtime_startups": 7,
    "prior_browser_startups": 6,
    "prior_observations_spent": 15,
    "cumulative_runtime_startup_limit": 8,
    "owned_runtime_root": "F:/nrl-auth118-owned-policy1",
    "expires_at": "2026-10-07T22:31:23.893263+00:00",
    "real_provider_free_windows": 1
  },
  "development_check_run_limit": 12,
  "development_correction_round_limit": 12,
  "mandatory_pytest_process_limit": 4,
  "owned_test_scratch_root": "F:\\reverse-agent-artifacts\\worktree-audit-20261002-56c5\\issue118-delegation-phase6-policy-recovery-20261007\\test-scratch",
  "cumulative_prior_development_checks": 8,
  "cumulative_prior_correction_rounds": 9,
  "cumulative_development_check_limit": 40,
  "cumulative_correction_round_limit": 33,
  "mandatory_check_run_limit": 12,
  "autonomy_policy_authority": {
    "schema_version": 1,
    "confirmation_mode": "DELEGATED_CONTROLLER",
    "personally_human": false,
    "controller_identity": "Codex/root under explicit Owner bounded-controller delegation",
    "upper_proposal_sha256": "1285c0b7787ad010cba92f4b31260c138fe138e1d447b8d26a1307a242911b0b",
    "upper_expires_at": "2026-10-07T22:31:23.893263+00:00",
    "phase_ordinal": 6,
    "policy_id": "issue118-delegated-checker-policy1",
    "policy_revision": 1,
    "policy": {
      "mode": "CONTROLLER_REVIEW",
      "repository": "dddd2024/Nerelan",
      "resourceAccess": {
        "filesystem": {
          "allowedPaths": [
            "frontend/src/components/sidebar.tsx"
          ],
          "writablePaths": []
        },
        "network": {
          "allowedDomains": [],
          "allowWrite": false
        },
        "shell": {
          "allowedCommands": [
            "git_diff_check"
          ],
          "deniedCommands": []
        },
        "secrets": {
          "access": "none",
          "allowedKeys": []
        },
        "workerApproval": {
          "required": false,
          "approvers": []
        }
      },
      "githubCapabilities": [],
      "publicationCapabilities": [],
      "publicationPolicy": {
        "allowedArtifactOrPackage": [],
        "allowedRegistry": [],
        "allowedRepository": [],
        "allowedEnvironment": []
      },
      "mergePolicy": {
        "allowedRepositories": [],
        "allowedBaseBranches": [],
        "requiredChecks": [],
        "allowedMergeMethods": [],
        "requireExactHead": true
      },
      "autonomousWindow": {
        "enabled": true,
        "startsAt": "2026-10-07T10:31:23.893263Z",
        "expiresAt": "2026-10-07T22:31:23.893263Z",
        "maxPrsOpened": 0,
        "maxMergesToMain": 0,
        "maxReleasesCreated": 0,
        "maxDeploysToEnvironment": 0,
        "stopConditions": [
          {
            "type": "budget_exhausted",
            "scope": "window"
          },
          {
            "type": "window_expired",
            "scope": "window"
          },
          {
            "type": "manual_stop",
            "scope": "window"
          },
          {
            "type": "authority_revoked",
            "scope": "window"
          }
        ]
      },
      "budgets": {
        "maxPrsOpened": 0,
        "maxMergesToMain": 0,
        "maxReleasesCreated": 0,
        "maxDeploysToEnvironment": 0
      }
    },
    "policy_digest_sha256": "aa3ed08239e15b52357835ce536db8cbae788e97b3d4f92f47638a3b23eaf6b8",
    "window_id": "issue118-delegated-checker-window1",
    "delegation_slot_id": "issue118-upper-20261007-realactivation-slot1",
    "slot_ordinal": 1,
    "max_real_window_activations": 1,
    "host_instance_id": "issue118-owned-policy1-host",
    "runtime_instance_kind": "acceptance",
    "database_path": "F:/nrl-auth118-owned-policy1/.platform_v1_runtime/tasks.sqlite3",
    "workspace_path": "F:/nrl-auth118-owned-policy1",
    "allowed_operations": [
      "validate_task"
    ],
    "validation_command_ids": [
      "git_diff_check"
    ],
    "validation_paths": [
      "frontend/src/components/sidebar.tsx"
    ],
    "max_tasks": 1,
    "max_retries": 0,
    "max_concurrent_tasks": 1,
    "model_call_limit": 0,
    "provider_call_limit": 0,
    "github_write_limit": 0,
    "goal_idempotency_key": "issue118-policy1-git-diff-check-goal1",
    "plan_task_id": "CHECK001"
  }
}
```
