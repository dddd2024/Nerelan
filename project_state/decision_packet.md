# Approved delegated viewport and truthful task-read phase2

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20261007_issue118_delegated_viewport_r3_v1",
  "round_id": "round_20261007_issue118_delegated_viewport_r3_v1",
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
  "decision_scope": "ISSUE118_DELEGATED_NATIVE_VIEWPORT_AND_TASK_READ_STATES",
  "source_issue": 118,
  "parent_issue": 90,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 Owner via approved bounded-controller-delegation; phase selected by delegated Codex controller",
  "approval_basis": "Owner explicitly replied \u6279\u51c6 to exact prospective 12-hour bounded-controller-delegation proposal on2026-10-07; frozen approved proposal SHA256 1285c0b7787ad010cba92f4b31260c138fe138e1d447b8d26a1307a242911b0b. No prior deadline/counter/failure rewritten.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "codex/issue118-delegated-native-r3-v1-20261007",
  "base_sha": "a103ee029b726e11e52d73db890c2d0c4f6db629",
  "activation_base_sha": "a103ee029b726e11e52d73db890c2d0c4f6db629",
  "starting_head": "a103ee029b726e11e52d73db890c2d0c4f6db629",
  "required_branch": "codex/issue118-delegated-viewport-r3-v1-20261007",
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
  "product_change_commit_limit": 2,
  "generated_governance_commit_limit": 0,
  "normal_push_attempt_limit": 3,
  "draft_pr_creation_limit": 1,
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
    "specification": "Fix confirmed default 1280x720 emulated private-client viewport: use native-window viewport null; meaningful existing Node lifecycle fixture must assert exact context options. Sidebar must distinguish loading/error/confirmed empty without exposing raw exception or claiming empty on read failure; existing sidebar tests cover states and preserved task ordering. Exactly four source/test paths below. Existing TaskStore SQLite persistence is reused; historical F:/reverse-agent DB is read-only (51 tasks/46 goals observed), never migrated/merged/modified. Task dispatch remains blocked on missing trusted policy compiler/confirmation; Codex fallback is explicit, no renderer local-owner/ACTIVATE activation. This phase does not implement full118 architecture.\nDevelopment allowance4 corrections/4 checks; mandatory max6 invocations: Node trusted-client tests <=900s, sidebar/frontend tests <=900s, relevant private-client/combined-host pytest <=900s, git diff --check <=120s plus current canonical gate checks. No weakening existing assertions. Product commits<=2, exact pushes<=3 (activation plus<=2implementation), one Draft, descriptions<=3. No source change after mandatory freeze except newly counted correction.\nOne fresh owned runtime F:/nrl-auth118-owned-native6, ports18887/18888/18889 must be free. Exact verified source manifest, existing cache read-only, isolated Vite cache only. One clone/stack/browser; dev-up<=180s; known Node/Edge hashes and valid Microsoft signature unchanged. Three native observations<=180s each: true homepage/settings/navigation and normal->maximized->normal native viewport screenshot/UIA bounding rectangles; actual frontend-frame Task API read200 with supported UIA prompt ValuePattern or identity-guarded native Unicode input (never SendKeys text through IME), verify actual prompt/output not hardcoded status; original owned browser close+original broker exit/readiness false<=25s. Capture owned pixels only; preserve maximized state except deliberate resize test, never restore normal just for capture. No credential/capability value reads, no external windows/system IME changes. Third close observation and one canonical cleanup<=120s remain required after diagnostic failure. OwnedJobs0/portsclosed/shareddep metadata afterproof. No startup retries within this consumed phase. Existing persistence fixture reopen tests are fixture evidence only; actual historical metadata is not restart acceptance. No task/window/model/provider dispatch or formal historical runtime mutation.\nNatural exact-head CI and independent read-only audit mandatory for final acceptance, no rerun/dispatch. Root serializes aggregate ledger. All limits are additional within same approved original upper expiry; no previous failures/counters rewritten. No Ready/merge/main/tag/release/deploy/dependencies/workflows/unknown binary/destructive shared operations. New successor only under same approved upper scope, expiry and remaining allowance.\n\n# Prospective bounded controller delegation \u2014 approval required\n\nThis proposal is not execution authority and does not change any activated Decision, previous expiry, spending, failure or PR acceptance. It addresses repeated permission requests by preauthorizing phase-specific renewal within one finite allowance, rather than resetting counters. Existing Path-B Decision/command-plan/preflight/readiness mechanisms remain mandatory.\n\n## Exact proposed upper scope\n\nRepository: dddd2024/Nerelan only. Goal remains the full project/GitHub backlog; this grant covers the next #118 architecture execution window and its #384 native-client/#811 continuation prerequisites, not completion of the whole backlog.\n\nFirst integration ref: codex/issue118-client-page-close-r3-v1-20261007, exact base874cdfc7848e7ebff22ec2d6bc226cf0fef2e035. A fresh codex/issue118-* branch and immutable Decision-only activation precede each implementation phase and its exact Draft snapshot. Successor phases may use only the exact verified head of the preceding approved planning phase; no implicit main fallback or history rewrite. Current main97d766d7253378c093c31ed29c990cb6921f2ae4 is observed, not a permitted landing target under this proposal.\n\nClock: one12-hour absolute window frozen at the first new activation; all successors retain that same expiry. Expired/terminal prior packets remain unchanged. At window expiry, affected execution stops and evidence/cleanup follow the explicit phase plan; no renewal beyond this upper window.\n\nDelegated approval: within the named scope, the controller may select exact files/checks and approve fresh bounded phase Decisions under this recorded Owner delegation, with transparent approved_by provenance identifying delegated Agent action. That does not constitute personal human review or independent acceptance. No per-step confirmation for already-granted corrections/checks/phase renewal.\n\nSource envelope: existing reverse_agent/platform_v1/**, frontend/src/**, frontend/tests/**, frontend/e2e/**, frontend/trusted-client.mjs, frontend/trusted-client.node-test.mjs, tests/platform_v1/**, relevant existing tests/test_trust_authorization_adapter.py and tests/test_planning_and_github_adapters.py, docs/local-client-session.md, AGENTS.md and docs/agents/governance-reference.md. Each activated phase must enumerate its actual exact file allowlist and forbid unlisted files; the envelope alone is not a staging allowance. Canonical Decision/gate artifacts use the existing mechanisms, with explicit staging grants only for the selected Decision activation; preserve generated gate deltas and unknown/dirty work. No new Gate/verifier/receipt family to manufacture acceptance.\n\n## Work and acceptance\n\n1. Resolve the missing native positive TaskAPI200 evidence on exact existing source. Choose UI controls by actual identity-bound supported patterns; register precise failure step/diagnostic without credentials. Verify foreground identity immediately before any native keyboard use. Capture only owned pixels. Preserve already-proven home/tasks/settings and real page-close lifecycle evidence; no test fixture presented as browser evidence. Source instrumentation, if genuinely required, needs an exact phase source allowlist and focused verification.\n2. Implement full Issue118 Phase A canonical policy/validation, trusted exact-policy Owner confirmation, server-derived upper authority and durable immutable activation. The frontend must not confer authority by filling local-owner/ACTIVATE/verified flags. Reuse applicable existing authority validators through a thin adapter; never invent a merge intent for non-merge activation. Retain mature private transport/SQLite/coordinator boundaries. Each Issue118 canonical field and capability has an explicit enforced/unsupported classification. Unsupported privileged adapters remain unavailable until their own implementation phase; denial alone is not full-product acceptance.\n3. Complete the receipt/morning-summary contract and recovery: totals over the full window, bounded paginated history with stable snapshot/cursor, immutable policy/actor/input/precondition/result/budget/evidence bindings, original spending after restart, durable claims and partial-side-effect reconciliation. More than200 and1000 receipts must not silently change totals or lose accessible history. Reuse the current store and receipt primitives; no second state replica or runtime.\n4. Existing #118 later adapter phases can be designed and implemented provider-free within remaining scope/allowance, with their own exact Decisions/Drafts/tests. Real mark-ready/merge/tag/release/package/container/deployment side effects are outside this grant. No claim that mock adapter tests prove real publication/production operation.\n\nProvider-free mandatory negative acceptance includes Owner/digest/material-edit mismatch, unknown/extra policy fields, repository/branch/path/capability widening, expiry, revision replay, exhausted/corrupted allowance, receipt persistence failure, stale candidate head/check, restart/partial side effect and unsupported capability. Existing checks cannot be weakened. Source fixtures and synthetic Owner/adapter inputs are explicitly distinguished from real runtime acceptance.\n\nRequired phase checks: applicable existing deterministic pytest/frontend/native Node tests, git diff --check, existing transition-preflight PRE_EXECUTION_AUTHORIZED, publication-readiness PUBLICATION_READY, original natural exact-head CI logs/JUnit, independent exact-head review. No repeated passed checks without change/failure/concern; no CI rerun/dispatch. No source change after the exact-head mandatory freeze without a newly counted correction/check cycle. All attempts and failures consume cumulative allowances.\n\nPrefer actual project Goal/Task implementation only when its real trusted authority/runtime can represent the phase and operate within this grant. If it cannot, record the actual capability failure or missing trusted-authority seam, then use Codex. Do not activate an unsafe caller-declared window to make the project appear eligible.\n\n## Additional finite allowances (not resets)\n\nSource corrections24; optional development invocations32; mandatory check invocations36; source/Draft phases6; Decision activations6; product commits12; exact non-main pushes18; new Drafts6; description updates18. Each phase derives smaller limits from the remaining aggregate ledger. Full pytest<=2400s, focused pytest<=900s, frontend/native suite<=900s per invocation; other static/Path-A checks<=120s unless separately enumerated lower bounded command is required. Budget is charged at start, not success.\n\nOwned runtime clones4/stack starts4/browser starts4; total native observation invocations12<=180s each; canonical identity-bound cleanups4<=120s. Each runtime uses a fresh explicitly named F:/nrl-auth118-owned-* directory, explicit free loopback ports, existing dependency cache without install/modification, isolated Vite cache and exact verified source/config manifest. Known executable hashes/Microsoft signature must freshly match; change stops that launch. No repeated launch under a consumed phase slot.\n\nSynthetic/provider-free test windows may be activated only in owned test databases. At most2 real provider-free autonomous-window activations are permitted only after the trusted exact-policy Owner confirmation/upper-authority seam passes its tests and the real policy binds this grant. No live model calls from repository/runtime code or executor/provider dispatch. The repository/runtime model limit remains0; authorized Codex implementation/review agents are distinct from product provider calls.\n\nWith prior recorded totals, maximum cumulative source corrections33 (=9+24), development checks40 (=8+32), owned runtime stack starts8 (=4+4), browsers7 (=3+4), observations18 (=6+12). Previous fixed deadlines and failed records are untouched. New allowance is available only after explicit approval and fresh activation.\n\nParallel work: explicitly permit up to3 subagents for implementation/read-only audit, with one independent exact-head auditor barred from editing the assessed implementation. No agent can approve its own head as independent acceptance. Workers inherit narrower phase scope and remaining allowance, never raw secrets or unrestricted approval authority.\n\n## Forbidden throughout\n\nNo main push, history rewrite, mark-ready/merge/auto-merge, tag/release/publication/deployment, dependency installation/update, workflows/.github mutation, runner/workflow dispatch or rerun, cross-repository writes, raw credentials/secrets, model/provider calls, unknown/hostile binary execution, broad cleanup/delete/reset/stash/restore/bulk-stage, or touching an unrelated active owner's task/runtime. Existing GitHub CLI may perform scoped repository observation and exact non-main push/Draft/description operations only; no raw credential access or new credential store.\n\nAny unavailable mandatory check, mandatory failure, scope/identity drift, unknown sensitive delta, exhausted allowance or expiry stops the affected operation. Preauthorized successors may handle in-scope product/infrastructure failures only with fresh immutable authority, same upper absolute expiry and remaining cumulative allowance; no reset. Do not represent Draft/CI/self-review as landing or full Issue118/full-goal completion.\n\nFROZEN_UPPER_EXPIRES=2026-10-07T22:31:23.893263+00:00",
    "completion_boundary": "Actual native resize/transport/lifecycle proof, exact-head checks/CI/audit; architecture and whole goal remain incomplete."
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
    "frontend/trusted-client.mjs",
    "frontend/trusted-client.node-test.mjs",
    "frontend/src/components/sidebar.tsx",
    "frontend/tests/task-first-sidebar.test.tsx"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "frontend/trusted-client.mjs",
    "frontend/trusted-client.node-test.mjs",
    "frontend/src/components/sidebar.tsx",
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
    "reverse_agent/platform_v1/unattended_coordinator.py",
    "reverse_agent/model_access/service.py",
    ".github/workflows/ci.yml",
    "frontend/src/lib/platform-client.ts",
    "frontend/src/lib/task-client.ts",
    "frontend/src/lib/repository-client.ts",
    "frontend/src/lib/goal-start-operation.ts",
    "frontend/src/lib/goal-continuation-operation.ts"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md",
    ".github/**",
    ".codex-skills/**",
    "reverse_agent/**",
    "dev-up.ps1",
    "dev-down.ps1",
    "pyproject.toml",
    "project_state/rounds/**",
    "project_state/mainline_merge_intents/**",
    "**/secrets/**",
    "**/.env",
    "**/auth.json",
    "tests/**",
    "docs/**"
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
      "Owned frontend18889/Task18887/Model18888/ephemeral relay only; model0/provider0/credential0; no other listeners."
    ],
    "github_control_plane_network_exceptions": [
      "Up to3 exact pushes codex/issue118-delegated-viewport-r3-v1-20261007, one Draft against codex/issue118-delegated-native-r3-v1-20261007@a103ee029b726e11e52d73db890c2d0c4f6db629, up to3 descriptions, scoped read-only original CI; no comments or other writes."
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
      "command": "Fix confirmed default 1280x720 emulated private-client viewport: use native-window viewport null; meaningful existing Node lifecycle fixture must assert exact context options. Sidebar must distinguish loading/error/confirmed empty without exposing raw exception or claiming empty on read failure; existing sidebar tests cover states and preserved task ordering. Exactly four source/test paths below. Existing TaskStore SQLite persistence is reused; historical F:/reverse-agent DB is read-only (51 tasks/46 goals observed), never migrated/merged/modified. Task dispatch remains blocked on missing trusted policy compiler/confirmation; Codex fallback is explicit, no renderer local-owner/ACTIVATE activation. This phase does not implement full118 architecture.\nDevelopment allowance4 corrections/4 checks; mandatory max6 invocations: Node trusted-client tests <=900s, sidebar/frontend tests <=900s, relevant private-client/combined-host pytest <=900s, git diff --check <=120s plus current canonical gate checks. No weakening existing assertions. Product commits<=2, exact pushes<=3 (activation plus<=2implementation), one Draft, descriptions<=3. No source change after mandatory freeze except newly counted correction.\nOne fresh owned runtime F:/nrl-auth118-owned-native6, ports18887/18888/18889 must be free. Exact verified source manifest, existing cache read-only, isolated Vite cache only. One clone/stack/browser; dev-up<=180s; known Node/Edge hashes and valid Microsoft signature unchanged. Three native observations<=180s each: true homepage/settings/navigation and normal->maximized->normal native viewport screenshot/UIA bounding rectangles; actual frontend-frame Task API read200 with supported UIA prompt ValuePattern or identity-guarded native Unicode input (never SendKeys text through IME), verify actual prompt/output not hardcoded status; original owned browser close+original broker exit/readiness false<=25s. Capture owned pixels only; preserve maximized state except deliberate resize test, never restore normal just for capture. No credential/capability value reads, no external windows/system IME changes. Third close observation and one canonical cleanup<=120s remain required after diagnostic failure. OwnedJobs0/portsclosed/shareddep metadata afterproof. No startup retries within this consumed phase. Existing persistence fixture reopen tests are fixture evidence only; actual historical metadata is not restart acceptance. No task/window/model/provider dispatch or formal historical runtime mutation.\nNatural exact-head CI and independent read-only audit mandatory for final acceptance, no rerun/dispatch. Root serializes aggregate ledger. All limits are additional within same approved original upper expiry; no previous failures/counters rewritten. No Ready/merge/main/tag/release/deploy/dependencies/workflows/unknown binary/destructive shared operations. New successor only under same approved upper scope, expiry and remaining allowance.",
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
        "frontend/trusted-client.mjs",
        "frontend/trusted-client.node-test.mjs",
        "frontend/src/components/sidebar.tsx",
        "frontend/tests/task-first-sidebar.test.tsx"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "native.validation",
      "command": "Node trusted-client test; sidebar/frontend Vitest; relevant private-client/combined-host pytest; git diff --check; current canonical gates; actual native observations and cleanup as specification.",
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
      "command": "Up to3 exact pushes codex/issue118-delegated-viewport-r3-v1-20261007, one Draft against codex/issue118-delegated-native-r3-v1-20261007@a103ee029b726e11e52d73db890c2d0c4f6db629, up to3 description updates; original natural CI scoped readonly.",
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
    "note": "Exactly new owned external runtime F:/nrl-auth118-owned-native6; no historical DB writes; exact source manifest with owned Vite cache delta only."
  },
  "workstream_id": "issue118-delegation-phase2-viewport-20261007",
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
  "pull_request_description_update_limit": 3,
  "runtime_acceptance_limits": {
    "clone": 1,
    "stack_start": 1,
    "browser_start": 1,
    "observations": 3,
    "normal_cleanup": 1,
    "source_corrections": 4,
    "source_checks_replay": 0,
    "prior_runtime_startups": 4,
    "prior_browser_startups": 3,
    "prior_observations_spent": 6,
    "cumulative_runtime_startup_limit": 8,
    "owned_runtime_root": "F:\\nrl-auth118-owned-native6",
    "expires_at": "2026-10-07T22:31:23.893263+00:00"
  },
  "development_check_run_limit": 4,
  "development_correction_round_limit": 4,
  "mandatory_pytest_process_limit": 2,
  "owned_test_scratch_root": "F:\\reverse-agent-artifacts\\worktree-audit-20261002-56c5\\issue118-delegation-phase2-viewport-20261007\\test-scratch",
  "cumulative_prior_development_checks": 8,
  "cumulative_prior_correction_rounds": 9,
  "cumulative_development_check_limit": 40,
  "cumulative_correction_round_limit": 33
}
```
