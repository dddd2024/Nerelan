# Bounded system Runs identity successor with frozen system input

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260927_runs_usage_identity_r2_v3",
  "round_id": "round_20260927_runs_usage_identity_r2_v3",
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
  "repository": "dddd2024/Nerelan",
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "decision_commit_must_precede_implementation": true,
  "decision_commit_must_precede_execution": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_immutability_check_required_in": [
    "transition_preflight",
    "transition_reconcile",
    "worktree_publication_readiness"
  ],
  "fresh_worktree_creation_required": true,
  "history_reuse_allowed": false,
  "provider_free_acceptance_required": true,
  "decision_scope": "RUNS_USAGE_AND_TASK_IDENTITY_ONLY",
  "source_issue": 999,
  "parent_issue": 448,
  "approved_by": "dddd2024 via explicit delegated Owner authorization",
  "approval_basis": "Owner delegates completion of all open and discovered tasks to the Nerelan system, supervisor audit and independent AI acceptance, with no token/cost cap. This bounded batch implements Issues999 and1001 in an isolated exact-base worker, keeping individual acceptance criteria. It permits known installed browser validation and existing launcher SourceDir/preview operation, not source deployment or landing. Product code/tests remain system-authored. Fresh bounded successor after actual live-browser identity collision, not a retroactive amendment: v1 remains immutable and unaccepted. Owner authorization includes newly discovered issues and system execution with independent supervisor acceptance. This successor explicitly imports the exact previously system-authored development candidate as an unaccepted input commit so the next worker can make a narrow incremental repair without rereading another worktree.",
  "risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "607d8daf72ec809cfe5d09bd2b5b7f711d9e294f",
  "activation_base_sha": "607d8daf72ec809cfe5d09bd2b5b7f711d9e294f",
  "starting_head": "607d8daf72ec809cfe5d09bd2b5b7f711d9e294f",
  "fresh_base": "607d8daf72ec809cfe5d09bd2b5b7f711d9e294f",
  "current_main_expected": "607d8daf72ec809cfe5d09bd2b5b7f711d9e294f",
  "required_branch": "codex/runs-usage-identity-r2-v3-20260927",
  "workstream_id": "runs-usage-identity-r2-v3",
  "follows_last_decision_id": "decision_20260927_issue997_windows_binding_env_r2_v1",
  "follows_last_round_id": "round_20260927_issue997_windows_binding_env_r2_v1",
  "workflow_profile": "baseline",
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 2,
  "generated_governance_commit_limit": 0,
  "normal_push_attempt_limit": 2,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "workflow_dispatch_limit": 0,
  "live_model_call_limit": 3,
  "provider_network_call_limit": 0,
  "credential_access_limit": 0,
  "local_browser_launch_limit": 12,
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
  "live_provider_access_allowed": true,
  "credential_access_allowed": false,
  "unknown_binary_execution_allowed": false,
  "model_api_invocation_allowed": true,
  "external_reverse_tool_invocation_allowed": false,
  "destructive_operations_allowed": false,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md"
  ],
  "bootstrap_exception_commands": [],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "frontend/src/routes/runs.tsx",
    "frontend/tests/runs.test.tsx",
    "frontend/e2e/runs.spec.ts",
    "frontend/src/lib/usage-presentation.ts",
    "frontend/tests/usage-presentation.test.ts",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "frontend/src/routes/runs.tsx",
    "frontend/tests/runs.test.tsx",
    "frontend/e2e/runs.spec.ts",
    "frontend/src/lib/usage-presentation.ts",
    "frontend/tests/usage-presentation.test.ts",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md",
    ".github/**",
    ".codex-skills/**",
    "reverse_agent/**",
    "dev-up.ps1",
    "dev-down.ps1",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/playwright.config.ts",
    "frontend/vite.config.ts",
    "frontend/e2e/snapshots/**",
    "project_state/mainline_merge_intents/**",
    "project_state/rounds/**",
    "pyproject.toml",
    "requirements*.txt"
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
    "credential_access",
    "unknown_binary_execution",
    "external_reverse_tool_invocation",
    "destructive",
    "tag_or_release",
    "dependency_install",
    "generated_governance_commit",
    "snapshot_generation_or_threshold_change",
    "fix_forward_after_mandatory_failure"
  ],
  "path_risk_floor": [
    {
      "pattern": "project_state/**",
      "minimum_risk": "R2"
    },
    {
      "pattern": "frontend/e2e/snapshots/**",
      "minimum_risk": "R3"
    }
  ],
  "semantic_implementation_contract": {
    "specification": "System completes Issues999/1001 using the exact five-file prior EB candidate as a frozen, explicitly unaccepted input. After Decision activation, passing existing gates and the first activation Draft, supervisor may copy only the five manifest-bound system-authored files and create one local input-artifact product commit. This is not final acceptance, deployment or publication. The worker must start at that exact recorded input commit and only repair same-title distinct-task identity using existing public task_id, with readable secondary visible identity and distinct accessible names. Include same-title/same-state, empty-title, different-task and responsive/keyboard regressions. Preserve all prior usage semantics, cost caveats, control permissions, real request-confirm steps, error/focus behavior and shared theme tokens. No backend/state/store/API/dependency/config/snapshot change. System authors all new product/test edits; supervisor transfers exact system output bytes and makes one final product commit after development verification. Total product commits two (input artifact + final correction). Detached worker materialization at the recorded input commit is permitted. No instructions/raw sensitive title fetch to disambiguate. Preserve root71records and all previous work.",
    "completion_boundary": "Exact-source frontend typecheck/tests/build, existing read-model regressions, installed Edge browser/keyboard/visual evidence, independent acceptance and natural exact-head CI. Fixtures, live dirty-root observations, candidate previews and source acceptance are distinguished. Draft only; later landing/deployment needs separate bounded authority. Product checks call no model/provider. All visible run toggles from the actual API must distinguish repeated titles by public task identity; the v1 live audit duplicate-label failure remains recorded. Input snapshot acceptance and native task verification are never inferred from source-independent tests. Product-source acceptance needs actual final-artifact evidence even if an earlier authoring task timed out."
  },
  "runtime_scratch_policy": {
    "paths": [
      ".platform_v1_runtime/**",
      "frontend/node_modules",
      "frontend/node_modules/**",
      "frontend/dist/**",
      "frontend/test-results/**",
      "frontend/playwright-report/**",
      "frontend/*.tsbuildinfo",
      "**/__pycache__/**",
      ".pytest_cache/**"
    ],
    "stage_allowed": false,
    "note": "Canonical/worker node_modules junction may point only to existing F:/reverse-agent/frontend/node_modules after identical package and lock manifests are verified. No install, dependency mutation or global env change. Temporary config/reports/screenshots remain under supervisor Temp artifacts. Root runtime stores/metadata change only through existing APIs/launcher. Preserve unknown files."
  },
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": true,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "bmad_installation_allowed": false,
    "network_access_default_allowed": false,
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [],
    "ci_network_exceptions": [
      "Unchanged natural CI package setup and provider-free checks only; no added workflow or manual dispatch."
    ],
    "trusted_worker_network_exceptions": [],
    "user_local_network_exceptions": [
      "Existing loopback Task/Model APIs and configured coding-glm trusted relay for at most3 system implementation/review tasks; no token/cost cap; one concurrent task and zero automatic retries. Provider-free local test servers and known installed Node/PowerShell/Python/Edge. Read-only browser Task API use during exact-source preview; no browser execution authority or credentials."
    ],
    "github_control_plane_network_exceptions": [
      "Canonical exact branch activation/implementation pushes and one Draft; descriptions only. No Ready/merge/tag/release under source stage."
    ]
  },
  "allowed_commands": [
    {
      "command_id": "runsux.bootstrap",
      "command": "Fresh full exact-base checkout F:/Nerelan-runs-ux-r2-v3-20260927 on codex/runs-usage-identity-r2-v3-20260927; commit only immutable Decision once. Existing startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre and worktree-publication-readiness via python -m reverse_agent.project_gate SUBCOMMAND --state-dir project_state. Require PRE_EXECUTION_AUTHORIZED/PUBLICATION_READY before product work; never stage generated gates.",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "local_static_check",
        "command_plan_generation",
        "commit",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "project_state/decision_packet.md"
      ],
      "produced_artifacts": [
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "runsux.system_input",
      "command": "Only after activation Draft exists and current existing gates pass: verify the frozen five-file SHA256 manifest in this Decision against canonical v1 EB source and its recorded system authors. Copy those exact bytes into this fresh publisher without edits; stage only the five exact source paths and create one local unaccepted system-input commit. Record commit/tree and unchanged Decision. Do not call it functional acceptance or publish it as completed work. This committed system artifact becomes the explicitly approved initial worker Git source; workers do not copy from any external worktree. Generated gates remain unstaged. No other candidate files or root dirty visual work may be imported.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "source_edit",
        "commit",
        "local_static_check",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "frontend/src/routes/runs.tsx",
        "frontend/tests/runs.test.tsx",
        "frontend/e2e/runs.spec.ts",
        "frontend/src/lib/usage-presentation.ts",
        "frontend/tests/usage-presentation.test.ts"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "runsux.runtime",
      "command": "After the input-artifact commit exists and no tasks are inflight, use unchanged Windows PowerShell5 F:/reverse-agent/dev-up.ps1 -RepoDir F:/reverse-agent -SourceDir F:/Nerelan-runs-ux-r2-v3-20260927 -OpenCodeModel sensenova-6.8-flash-lite -NoBrowser. Preserve public models/timeouts, stores and ports. Prior v1 window is BLOCKED/usage_unknown after task timeout; preserve that record, do not alter its usage/status. Owner delegates a new separate bounded window for at most3 new tasks with no monetary/token cap, maxone concurrent, zero automatic retry; this does not reinterpret unknown usage as zero or weaken enforcement. Set execution/planning SHA to the exact recorded system-input commit. Verify worker starts at that commit. Only launcher-verified owned processes may restart. On failure restore prior SourceDir v1 with unchanged launcher and preserved environment.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "local_static_check",
        "machine_specific_execution",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "runsux.system",
      "command": "Dispatch at most3 fresh scoped implementation/review tasks via existing Task API/coding-glm from the exact system-input commit, one concurrent, zero automatic retry, no token/cost cap. Only system authors new edits in the five allowed files; no external-worktree access/commit/push or config changes. Native functional profiles may verify actual changes; a model report is not acceptance. Supervisor copies exact system file bytes, independently reviews scope and tests/browser results, then creates one final product commit. Known installed tools only; process-local PATHEXT workaround; no install or global environment change. Preserve the v1 authoring timeout, unknown usage and failed live identity audit without laundering their status.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "source_edit",
        "commit",
        "local_static_check",
        "machine_specific_execution",
        "model_api_invocation",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "frontend/src/routes/runs.tsx",
        "frontend/tests/runs.test.tsx",
        "frontend/e2e/runs.spec.ts",
        "frontend/src/lib/usage-presentation.ts",
        "frontend/tests/usage-presentation.test.ts"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "runsux.checks",
      "command": "Verify frontend package.json/package-lock.json identical to existing root dependency installation before creating canonical/worker frontend/node_modules junction only to that existing directory. Run npm --prefix frontend run typecheck, npm --prefix frontend test, npm --prefix frontend run build, python -B -m pytest tests/platform_v1/test_run_read_model.py -q -p no:cacheprovider and git diff --check on final source. Development corrections precede final mandatory checks. No install, provider calls, manifest/lock edits or weakening tests.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "unit_test",
        "integration_test",
        "build",
        "local_static_check",
        "diff_validation",
        "machine_specific_execution",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "runsux.browser",
      "command": "Known installed msedge/Playwright only, at most12 launches. Use isolated source Vite preview on free loopback4174 and external Playwright config inheriting unchanged repository config, exact testDir, installed msedge, fixed desktop1440x900/mobile390x844 and light/dark themes; no snapshot baseline writes. Run scoped Runs E2E with disclosed fixture data. For real Task API browser validation, after all model tasks finish, temporarily replace only verified-owned frontend4173 process with exact-source Vite at4173; preserve Task/Model API processes/stores, record PID/executable/starttime, use read-only UI actions. Stop only that verified preview and restore root frontend with unchanged existing launcher and current SourceDir, with no active tasks. If ownership/port validation fails, do not kill unknown processes; retain blocked live-path evidence. Capture/view exact-source screenshots, keyboard expansion, titles/usage/controls, overflow; distinguish fixture/live and preview/deployment. No browser shell/filesystem/policy authority.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "integration_test",
        "local_static_check",
        "machine_specific_execution",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "runsux.publish",
      "command": "Push only codex/runs-usage-identity-r2-v3-20260927 at mosttwice total (activation, oneimplementation) and create/update one Draft against main locked at607d8daf72ec809cfe5d09bd2b5b7f711d9e294f. Before each push require publication readiness, exact main/base and scope, no concurrent branch mutation. Draft before any source changes. Bind immutable Decision/exact head and truthful evidence. No Ready/merge/deployment.",
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
    },
    {
      "command_id": "runsux.ci",
      "command": "Observe existing natural CI, Decision Preflight, State Gate and applicable frontend workflow. Zero provider/model calls in checks. No reruns/dispatch or workflow/dependency edits. Inspect native diagnostic, not only wrapper green.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "ci_only",
      "operations": [
        "unit_test",
        "integration_test",
        "local_static_check",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "runsux.audit",
      "command": "Independent exact-head source/visual audit, distinct acceptance for999 and1001. Preserve current root, other PRs and scratch; report actual tests and unavailable checks. Exact source acceptance is not deployment/landing.",
      "phase": "final_evidence",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "remote_observation",
      "operations": [
        "code_read",
        "read_only_audit",
        "repository_observation"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "concurrent_work_preservation": {
    "prs": [
      991,
      992,
      995,
      1000,
      1003
    ],
    "root_branch": "owner/20260926-defect11-rootcause-and-frontend-focus",
    "root_head": "22ece480512a5ad14205db1a7bc436fdc4a123ce",
    "policy": "Preserve root71statusrecords, active landing evidence and unrelated PR heads. No adoption or publication of root dirty frontend/brand changes. No mutation of1002 backend state contract in this batch. Preserve sourceDraft1003 activation3e15e4 and its uncommitted EB candidate; no source publication from v1 during this successor."
  },
  "reference_paths": [
    "AGENTS.md",
    "docs/agents/governance-reference.md",
    "dev-up.ps1",
    "frontend/src/lib/platform-client.ts",
    "frontend/src/lib/format.ts",
    "frontend/src/types/index.ts",
    "frontend/e2e/fixtures.ts",
    "frontend/playwright.config.ts",
    "frontend/vite.config.ts",
    "reverse_agent/platform_v1/run_read_model.py",
    "reverse_agent/platform_v1/run_store.py"
  ],
  "source_issues": [
    999,
    1001
  ],
  "system_input_artifact": {
    "status": "UNACCEPTED_DEVELOPMENT_INPUT",
    "sha256_by_path": {
      "frontend/src/routes/runs.tsx": "7bec224af43f4838586d184adb2eb801f8c3ab3c32d86a95ef0ee6c771d9ad31",
      "frontend/tests/runs.test.tsx": "958cecbfeb13a17cfde7949c34aa36e3f1229d70f3c223999011ab1cebf1dee8",
      "frontend/e2e/runs.spec.ts": "b2c72f7e848687827471fa34f83249dbefd6328fa1e725a49d7f7d65bd45f1a8",
      "frontend/src/lib/usage-presentation.ts": "8df6bf80672ff1a21e6f9b9c2e0a083e96e7818d0d196266dec1913e8f6ba1d9",
      "frontend/tests/usage-presentation.test.ts": "bc251e53dc93f273589383ed76e8bdfca937a51ac4c2115571e5ace1b78719ec"
    },
    "system_author_by_path": {
      "frontend/src/routes/runs.tsx": "task-1790514699074-5e58b5a33c13",
      "frontend/tests/runs.test.tsx": "task-1790514699074-5e58b5a33c13",
      "frontend/e2e/runs.spec.ts": "task-1790511398586-de8c0d42bd6c",
      "frontend/src/lib/usage-presentation.ts": "task-1790514699074-5e58b5a33c13",
      "frontend/tests/usage-presentation.test.ts": "task-1790514699074-5e58b5a33c13"
    },
    "prior_checks": "Independent458Vitest checks and10mockE2E checks passed. Real API had duplicate names(5same-title queued,2same-title failed); v1 not accepted. TaskE timed out2700seconds; native validation did not run. Those facts stay unchanged.",
    "prior_source_draft": 1003,
    "prior_source_activation": "3e15e4a472d9d2f438b2687897b66ee06ffcb6e8"
  },
  "supersedes_unaccepted_decision_id": "decision_20260927_runs_usage_identity_r2_v1",
  "prior_unpublished_authority_failure": "v2 activation695503f2c2be14ead6164905da3180c7998a062a failed command-plan generation because system_input omitted registered machine_specific_execution for user_local. No source was imported, no model dispatched, no push/Draft created. Preserve v2 unchanged. v3 only corrects this explicit operation declaration."
}
```
