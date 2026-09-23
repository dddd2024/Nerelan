# Approved bounded system repair of timeout evidence

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260923_ux14_timeout_evidence_r3_v1",
  "round_id": "round_20260923_ux14_timeout_evidence_r3_v1",
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
  "decision_scope": "SUPERVISED_SYSTEM_AUTHORED_UX14_TIMEOUT_EVIDENCE",
  "source_issue": 448,
  "parent_issue": 260,
  "approved_by": "dddd2024 via explicit delegated Owner completion",
  "approval_basis": "User explicitly delegated Owner completion to the supervisor while retaining the original separation: Nerelan authors product repairs, supervisor inspects and assigns tasks. Independent candidate boundary review accepted SHA256 d60a5834a7fe8e78b5bdf30af8394fcf3d95e27847ea2e48bfd19464be6b85a1. This separately scoped round authorizes one new bounded UX14 timeout-evidence implementation task with existing coding-agnes/agnes-3.0-flash/OpenCode/single and300-second process timeout, actual activation/preflight, independent exact-artifact acceptance and local preview only. It is not a UX05 retry or root-cause claim. No GitHub publication, credential access, model fallback/retry, budget extension or supervisor-authored product fixes.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R3",
  "integration_base_ref": "codex/ux05-system-modal-r3-v1-20260923",
  "base_sha": "de2305bc29b18c90bbb293cbdda22a8d8bc0565f",
  "activation_base_sha": "de2305bc29b18c90bbb293cbdda22a8d8bc0565f",
  "starting_head": "de2305bc29b18c90bbb293cbdda22a8d8bc0565f",
  "fresh_base": "de2305bc29b18c90bbb293cbdda22a8d8bc0565f",
  "current_main_expected": "58d4068f43ca4914b122445685cae410a8fa156e",
  "required_branch": "codex/ux14-timeout-evidence-r3-v1-20260923",
  "workstream_id": "ux14-timeout-evidence-r3-v1",
  "follows_last_decision_id": "decision_20260923_ux05_system_modal_r3_v1",
  "follows_last_round_id": "round_20260923_ux05_system_modal_r3_v1",
  "workflow_profile": "browser_r3",
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 1,
  "generated_governance_commit_limit": 0,
  "normal_push_attempt_limit": 0,
  "draft_pr_creation_limit": 0,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "workflow_dispatch_limit": 0,
  "credential_access_limit": 0,
  "local_browser_launch_limit": 2,
  "pr_creation_allowed": false,
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
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/platform_v1/durable_execution.py",
    "tests/platform_v1/test_timeout_evidence.py",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/platform_v1/durable_execution.py",
    "tests/platform_v1/test_timeout_evidence.py",
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
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/e2e/snapshots/**",
    "project_state/mainline_merge_intents/**",
    "project_state/rounds/**",
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
    "specification": "System alone changes the three named product paths. Preserve bounded redacted TimeoutExpired partial bytes/str/None output and stderr through existing event/evidence/usage interfaces; distinguish valid complete events from incomplete/truncated/absent output, bound total size/count and prevent secret persistence. Persist failed single-executor changed files under current durable fencing without success checkpoint advance. Retain FAILED timeout, no validation if none ran, unchanged300-second budget, no retry and unchanged lease semantics. No live streaming, new store/schema, dependencies, credential/config reads or frontend repair in this round. Do not claim to reconstruct lost UX05 output or fix its unknown root cause.",
    "completion_boundary": "System-authored artifact, mandatory provider-free checks, immutable exact commit, independent exact-head acceptance. Only then optional local runtime preview through the two named fast-forwards. No GitHub publication or all-product acceptance."
  },
  "runtime_scratch_policy": {
    "paths": [
      "frontend/node_modules/**",
      "frontend/dist/**",
      "**/__pycache__/**",
      ".pytest_cache/**",
      ".platform_v1_runtime/**"
    ],
    "stage_allowed": false,
    "note": "Only existing runtime scratch and new named child workspaces under F:/Nerelan-first-use-task-workspaces-20260923; audit artifacts in the existing nerelan-audit directory. Reuse installed frontend dependencies by a narrow node_modules junction after exact package+lock equality; no install. Never stage scratch or inspect auth/config/credential files."
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
    "ci_network_exceptions": [],
    "trusted_worker_network_exceptions": [],
    "user_local_network_exceptions": [
      "Freshly verify exact accepted UX05 host base de2305bc29b18c90bbb293cbdda22a8d8bc0565f, failed child clean identity, original workspace ownership, runtime terminal state and immutable prior source evidence; bounded read-only GitHub main/PR991 observation only. Independently review this candidate and final approval-only transformation under existing user Owner delegation. Create only F:/Nerelan-ux14-timeout-evidence-20260923 on codex/ux14-timeout-evidence-r3-v1-20260923 from exact local integration base. Commit independently accepted approved Decision only once, generate actual startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre and worktree-publication-readiness; require PRE_EXECUTION_AUTHORIZED/PUBLICATION_READY and independent exact activation check. No product edit or model before that.",
      "Before and after EACH service restart and immediately before dispatch require live supported-API observations active_window=null, coordinator.inflight_batch=false, no running/executing task and no login flow in progress; dev-up enables the coordinator and existing windows must not cause any queued dispatch. If any predicate fails stop the affected action without cancelling other work or altering window state. After independent Decision-only activation acceptance, verify clean runtime branch codex/first-use-20260923 at de2305bc29b18c90bbb293cbdda22a8d8bc0565f, exact owned PID/executable/start-time/source/runtime identity and package-lock equality. Use existing dev-down/dev-up hidden NoBrowser for only owned services. First of two authorized local --ff-only runtime synchronizations moves to exact activation commit. SourceDir becomes F:/Nerelan-ux14-timeout-evidence-20260923, execution_authority_sha and planning_sha equal exact activation. Keep current runtime database, all tasks/goals/Inbox/config/bindings and external task root. No raw config/credential reads, installs, provider calls or settings changes in this step; verify new head/tree and launch provenance.",
      "Before and after EACH service restart and immediately before dispatch require live supported-API observations active_window=null, coordinator.inflight_batch=false, no running/executing task and no login flow in progress; dev-up enables the coordinator and existing windows must not cause any queued dispatch. If any predicate fails stop the affected action without cancelling other work or altering window state. After exact host evidence verification and saved coding-agnes/agnes-3.0-flash/opencode binding readback, create and execute exactly one NEW UX14 Task via existing loopback API8766. branch=exact accepted activation commit, single mode, existing300-second process limit and <=256KiB instruction with complete approved host evidence. Nerelan alone authors the three permitted product files. No UX05 retry, other model, fallback, autonomous window or publication; no direct CLI model call. Child may run scoped provider-free checks if available, otherwise report unavailable without installs. Do not regenerate child Gates or access host paths.",
      "Observe that same Task via supported API and real browser until terminal. Preserve exact task/run/child HEAD/Decision identity and all changed paths. Independent audit all system output before transferring exact accepted bytes of only the three allowed product paths to host. Supervisor writes no implementation. Failure with no acceptable patch ends this round; no retry, increasing timeout, fix-forward, weaker checks or speculative root-cause claims.",
      "Before and after EACH service restart and immediately before dispatch require live supported-API observations active_window=null, coordinator.inflight_batch=false, no running/executing task and no login flow in progress; dev-up enables the coordinator and existing windows must not cause any queued dispatch. If any predicate fails stop the affected action without cancelling other work or altering window state. Only after mandatory exact-head checks and independent acceptance, verify owned service identity and clean ancestor runtime; second and last --ff-only advances runtime to accepted system commit. Existing dev-up hidden NoBrowser uses F:/Nerelan-ux14-timeout-evidence-20260923 as SourceDir and that exact authority/planning SHA. Preserve all user data/settings and verify after restart. Use actual loopback API/Edge for existing failed historical UX05 state without rerunning it. Provider-free fake-process/HTTP tests prove new failure evidence behavior; do not claim historical lost output recovered or live-provider root cause solved. Keep all UX tickets including05 open until their own acceptance. No GitHub writes, deployment or publication."
    ],
    "github_control_plane_network_exceptions": []
  },
  "allowed_commands": [
    {
      "command_id": "ux14v1.bootstrap",
      "command": "Freshly verify exact accepted UX05 host base de2305bc29b18c90bbb293cbdda22a8d8bc0565f, failed child clean identity, original workspace ownership, runtime terminal state and immutable prior source evidence; bounded read-only GitHub main/PR991 observation only. Independently review this candidate and final approval-only transformation under existing user Owner delegation. Create only F:/Nerelan-ux14-timeout-evidence-20260923 on codex/ux14-timeout-evidence-r3-v1-20260923 from exact local integration base. Commit independently accepted approved Decision only once, generate actual startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre and worktree-publication-readiness; require PRE_EXECUTION_AUTHORIZED/PUBLICATION_READY and independent exact activation check. No product edit or model before that.",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "commit",
        "command_plan_generation",
        "local_static_check",
        "machine_specific_execution",
        "network_access"
      ],
      "network_access": true,
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
      "command_id": "ux14v1.runtime",
      "command": "Before and after EACH service restart and immediately before dispatch require live supported-API observations active_window=null, coordinator.inflight_batch=false, no running/executing task and no login flow in progress; dev-up enables the coordinator and existing windows must not cause any queued dispatch. If any predicate fails stop the affected action without cancelling other work or altering window state. After independent Decision-only activation acceptance, verify clean runtime branch codex/first-use-20260923 at de2305bc29b18c90bbb293cbdda22a8d8bc0565f, exact owned PID/executable/start-time/source/runtime identity and package-lock equality. Use existing dev-down/dev-up hidden NoBrowser for only owned services. First of two authorized local --ff-only runtime synchronizations moves to exact activation commit. SourceDir becomes F:/Nerelan-ux14-timeout-evidence-20260923, execution_authority_sha and planning_sha equal exact activation. Keep current runtime database, all tasks/goals/Inbox/config/bindings and external task root. No raw config/credential reads, installs, provider calls or settings changes in this step; verify new head/tree and launch provenance.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "machine_specific_execution",
        "network_access",
        "source_edit"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "project_state/decision_packet.md"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "ux14v1.dispatch",
      "command": "Before and after EACH service restart and immediately before dispatch require live supported-API observations active_window=null, coordinator.inflight_batch=false, no running/executing task and no login flow in progress; dev-up enables the coordinator and existing windows must not cause any queued dispatch. If any predicate fails stop the affected action without cancelling other work or altering window state. After exact host evidence verification and saved coding-agnes/agnes-3.0-flash/opencode binding readback, create and execute exactly one NEW UX14 Task via existing loopback API8766. branch=exact accepted activation commit, single mode, existing300-second process limit and <=256KiB instruction with complete approved host evidence. Nerelan alone authors the three permitted product files. No UX05 retry, other model, fallback, autonomous window or publication; no direct CLI model call. Child may run scoped provider-free checks if available, otherwise report unavailable without installs. Do not regenerate child Gates or access host paths.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "machine_specific_execution",
        "network_access",
        "model_api_invocation",
        "source_edit",
        "unit_test",
        "integration_test",
        "diff_validation"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/platform_v1/opencode_executor.py",
        "reverse_agent/platform_v1/durable_execution.py",
        "tests/platform_v1/test_timeout_evidence.py"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "ux14v1.observe",
      "command": "Observe that same Task via supported API and real browser until terminal. Preserve exact task/run/child HEAD/Decision identity and all changed paths. Independent audit all system output before transferring exact accepted bytes of only the three allowed product paths to host. Supervisor writes no implementation. Failure with no acceptable patch ends this round; no retry, increasing timeout, fix-forward, weaker checks or speculative root-cause claims.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "source_edit",
        "read_only_audit",
        "diff_validation",
        "machine_specific_execution",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/platform_v1/opencode_executor.py",
        "reverse_agent/platform_v1/durable_execution.py",
        "tests/platform_v1/test_timeout_evidence.py"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "ux14v1.validate",
      "command": "Run the exact system-authored artifact checks: python -m pytest tests/platform_v1/test_timeout_evidence.py tests/platform_v1/test_opencode_executor.py tests/platform_v1/test_opencode_server_transport.py tests/platform_v1/test_execution_runtime_budget.py tests/platform_v1/test_durable_execution.py tests/platform_v1/test_durable_execution_v5.py tests/platform_v1/test_task_service.py -q; git diff --check. Tests must include partial timeout output bytes/str/None, malformed/truncated/huge output, synthetic secrets and size caps, usage/evidence deduplication, FAILED timeout/no validation, lease release and unchanged deadlines; failed tracked/untracked artifacts through durable/Task API, stale fence rejects writes; success/nonzero/server/durable paths remain valid. At most two development checks without supervisor source edits. After passing, commit exactly one system-product change, repeat the same checks on exact HEAD and base-to-head diff check; regenerate actual startup/plan/lint/preflight/readiness and obtain independent exact-head acceptance. Any mandatory failure stops synchronization and model actions.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "unit_test",
        "integration_test",
        "diff_validation",
        "commit",
        "command_plan_generation",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/platform_v1/opencode_executor.py",
        "reverse_agent/platform_v1/durable_execution.py",
        "tests/platform_v1/test_timeout_evidence.py"
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
      "command_id": "ux14v1.retest",
      "command": "Before and after EACH service restart and immediately before dispatch require live supported-API observations active_window=null, coordinator.inflight_batch=false, no running/executing task and no login flow in progress; dev-up enables the coordinator and existing windows must not cause any queued dispatch. If any predicate fails stop the affected action without cancelling other work or altering window state. Only after mandatory exact-head checks and independent acceptance, verify owned service identity and clean ancestor runtime; second and last --ff-only advances runtime to accepted system commit. Existing dev-up hidden NoBrowser uses F:/Nerelan-ux14-timeout-evidence-20260923 as SourceDir and that exact authority/planning SHA. Preserve all user data/settings and verify after restart. Use actual loopback API/Edge for existing failed historical UX05 state without rerunning it. Provider-free fake-process/HTTP tests prove new failure evidence behavior; do not claim historical lost output recovered or live-provider root cause solved. Keep all UX tickets including05 open until their own acceptance. No GitHub writes, deployment or publication.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "integration_test",
        "local_static_check",
        "machine_specific_execution",
        "network_access",
        "source_edit"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "project_state/decision_packet.md",
        "reverse_agent/platform_v1/opencode_executor.py",
        "reverse_agent/platform_v1/durable_execution.py",
        "tests/platform_v1/test_timeout_evidence.py"
      ],
      "produced_artifacts": []
    }
  ],
  "reference_paths": [
    "AGENTS.md",
    "docs/agents/governance-reference.md",
    "reverse_agent/platform_v1/task_runtime.py",
    "reverse_agent/platform_v1/run_store.py",
    "tests/platform_v1/test_opencode_executor.py",
    "tests/platform_v1/test_durable_execution.py",
    "tests/platform_v1/test_durable_execution_v5.py",
    "dev-up.ps1",
    "dev-down.ps1"
  ],
  "system_task_attempt_limit": 1,
  "system_execution_timeout_seconds": 300,
  "gpt_model_invocation_limit": 0,
  "model_budget_semantics": "Exactly one manually assigned new UX14 implementation task through existing coding-agnes binding to agnes-3.0-flash/OpenCode/single, existing300-second executor timeout. No other provider, retry/fallback, UX05 relaunch, autonomous window, queued task dispatch, settings/credential/OAuth changes or token/cost hard-cap claim. Token/cost observations remain factual; multiple provider exchanges inside this one task are possible.",
  "source_inbox_id": "inbox-1790158620782-05e360330915",
  "runtime_only_path_boundary": {
    "paths": [
      "project_state/decision_packet.md",
      "reverse_agent/platform_v1/opencode_executor.py",
      "reverse_agent/platform_v1/durable_execution.py",
      "tests/platform_v1/test_timeout_evidence.py"
    ],
    "checkout": "F:/Nerelan-first-use-20260923",
    "restriction": "Exact accepted local fast-forward only: de2305bc to Decision-only activation, then to independently accepted system product commit. Preserve DB/settings and old worktrees. No supervisor-authored product changes."
  },
  "host_child_authority_handoff": "Host activation contains this immutable approved Decision only above exact accepted de2305bc. Verify fresh real plan/preflight/readiness and independent activation check. The one detached child must derive from the exact activation commit; task embeds complete original host plan/preflight bytes, paths and SHA256, branch/head and Decision digest. Child verifies HEAD/Decision and cannot regenerate Gate files, read outside child or treat old child Gate files as current authority. Preserve host proof bytes until patch collection.",
  "concurrent_work_preservation": {
    "main": "58d4068f43ca4914b122445685cae410a8fa156e",
    "991": "f015eed511e3b1226e7ef1f2db22dd5b26fe47f5",
    "989_source_head": "ad18e253183fdf0d4e10f3f6e2c2054af0e22332",
    "988_source_head": "6e9f156a543293f37abc19a2dba6bc7b7364a852",
    "policy": "Read-only preserve all prior branches/worktrees including failed UX05 child, #988/#989/#990 and original workspace; no takeover or source transfer. Fresh source/base/runtime identities must match. Remote main/PR991 observation is context only, not authority for this independent accepted local-base successor.",
    "ux05_host_head": "de2305bc29b18c90bbb293cbdda22a8d8bc0565f",
    "ux05_child": "F:/Nerelan-first-use-task-workspaces-20260923/task-1790157323936-ed09d6308845"
  },
  "source_objective_sha256": "9a1a5be663a4975f0e2dbc798108ff5822130979332e2230700e21593d32f216",
  "runtime_activation_guard": "Before and after EACH service restart and immediately before dispatch require live supported-API observations active_window=null, coordinator.inflight_batch=false, no running/executing task and no login flow in progress; dev-up enables the coordinator and existing windows must not cause any queued dispatch. If any predicate fails stop the affected action without cancelling other work or altering window state. ",
  "local_fast_forward_boundary": "merge_allowed=false and forbidden merge mean no GitHub landing or non-fast-forward/history mutation. Exactly two local --ff-only runtime synchronizations are expressly permitted as described, with clean exact source/destination, ancestry and post-tree/head verification; no merge commit or other ref update.",
  "accepted_base_evidence": {
    "head": "de2305bc29b18c90bbb293cbdda22a8d8bc0565f",
    "review_path": "C:\\Users\\wjc27\\.codex\\visualizations\\2026\\09\\23\\01a0cd45-5b28-7132-8f0e-7daa29cd0350\\nerelan-audit\\ux05-prerequisite-exact-independent-review.json",
    "review_sha256": "9f43fef02397472c0245ffdd45c61ecbca86e393ea55c30890f9dd31db737576",
    "scope": "Existing exact prerequisite source/test acceptance, not UX05 or UX14 repair acceptance. Activation changes only Decision, so no reimport/re-edit prerequisite."
  }
}
```

