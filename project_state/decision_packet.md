# Approved bounded execution runtime recovery

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260923_issue989_execution_runtime_budget_r3_v1",
  "round_id": "round_20260923_issue989_execution_runtime_budget_r3_v1",
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
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R3",
  "integration_base_ref": "main",
  "base_sha": "58d4068f43ca4914b122445685cae410a8fa156e",
  "activation_base_sha": "58d4068f43ca4914b122445685cae410a8fa156e",
  "starting_head": "58d4068f43ca4914b122445685cae410a8fa156e",
  "fresh_base": "58d4068f43ca4914b122445685cae410a8fa156e",
  "current_main_expected": "58d4068f43ca4914b122445685cae410a8fa156e",
  "follows_last_decision_id": "decision_20260923_issue982_gpt_oauth_network_r3_v1",
  "follows_last_round_id": "round_20260923_issue982_gpt_oauth_network_r3_v1",
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 1,
  "generated_governance_commit_limit": 0,
  "normal_push_attempt_limit": 0,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "workflow_dispatch_limit": 0,
  "credential_access_limit": 0,
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
  "credential_access_allowed": false,
  "unknown_binary_execution_allowed": false,
  "external_reverse_tool_invocation_allowed": false,
  "destructive_operations_allowed": false,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md"
  ],
  "bootstrap_exception_commands": [],
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
    "fix_forward_after_mandatory_failure",
    "model_api_invocation",
    "provider_network_call",
    "oauth_operation",
    "runtime_restart",
    "browser_launch",
    "old_worktree_cleanup"
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
  "decision_scope": "PROVIDER_FREE_EXECUTION_RUNTIME_PREREQUISITE_REPAIR",
  "source_issue": 989,
  "parent_issue": 260,
  "approved_by": "dddd2024 via explicit delegated Owner execution",
  "approval_basis": "User explicitly authorizes supervisor fallback when system cannot complete. Actual Issue988 attempt failed with no product patch. Independently reviewed exact candidate 67d531028eb72654122617400fdd03f13499aecf66e666694af7fcfa4abce166. This bounded round permits supervisor repair of execution lease lifetime and minimal Windows environment with provider-free checks and Draft-only publication. No models, credentials, runtime restart or landing.",
  "required_branch": "codex/execution-runtime-budget-r3-v1-20260923",
  "workstream_id": "issue989-execution-runtime-budget-r3-v1",
  "workflow_profile": "baseline",
  "live_provider_access_allowed": false,
  "model_api_invocation_allowed": false,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "oauth_operation_limit": 0,
  "local_browser_launch_limit": 0,
  "system_task_attempt_limit": 0,
  "runtime_restart_limit": 0,
  "development_check_round_limit": 8,
  "windows_probe_invocation_limit": 6,
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/platform_v1/trusted_host.py",
    "reverse_agent/model_access/credential_relay.py",
    "tests/platform_v1/test_opencode_executor.py",
    "tests/platform_v1/test_execution_runtime_budget.py",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/platform_v1/trusted_host.py",
    "reverse_agent/model_access/credential_relay.py",
    "tests/platform_v1/test_opencode_executor.py",
    "tests/platform_v1/test_execution_runtime_budget.py",
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
  "semantic_implementation_contract": {
    "specification": "Supervisor authors the minimal prerequisite repair after the independently observed system failure. Pass the actual bounded CLI/server executor budget into execution-scoped relay lease creation or one-time pre-execution deadline binding; retain finite validation/hard cap and existing release on success/error/timeout/cancellation. Reject bool, NaN, infinity, nonpositive or excessive budgets before dispatch/lease issuance. Test request at120+seconds remains valid within a300-second task deadline, expiry at the precisely bound deadline including at most30seconds permitted setup margin rejects, released leases reject immediately, connection/model identity and existing secret confinement remain intact. Reject repeated deadline binding and any revival of expired or released leases. Do not silently extend deadlines, renew indefinitely, inject upstream keys into child env, or weaken existing tests. Repair only minimal Windows non-secret environment necessary for installed Git/cmd/PowerShell; retain allowlist isolation and do not copy full parent environment. Scope OpenCode edits to budget-to-lease and constrained child environment, trusted_host edits to matching bounded lease provider, credential_relay edits to finite bounds/expiry; no assistant evidence, prompt, UI, task scheduling or authorization refactor.",
    "completion_boundary": "Provider-free exact-head source acceptance and Draft publication only. No deployment/runtime restart, new system execution, OAuth, GPT/Codex/model invocation, title/UI repair, answer evidence repair or overall completion. A future independently authorized stage must validate and hand implementation back to Nerelan."
  },
  "runtime_budget_contract": {
    "default_executor_seconds": 300,
    "generic_default_lease_seconds": 120,
    "finite_execution_hard_cap_seconds": 3600,
    "maximum_setup_margin_seconds": 30,
    "finite_lease_hard_cap_seconds": 3630,
    "deadline_semantics": "Retain default executor300 and generic lease120seconds. Bind once before actual CLI/server invocation from validated executor timeout plus at most30seconds setup margin, or equivalent bounded deadline provider API. Only finite positive execution durations <=3600seconds; total execution-scoped lease lifetime <=3630seconds. No recurring renewal, revival of expired/released lease, unlimited grace, or global default extension. Reject expired deadlines/clock ambiguity instead of extending them.",
    "tests": "Synthetic snapshots/fake clock only. Prove request after120seconds succeeds within300-second task; expiry after exact configured deadline plus bounded margin rejects; release immediately rejects. Prove nondefault actual CLI/server timeouts reach binding and release on success/error/timeout/cancellation. Validate NaN/infinity/bool/negative/excessive values before side effects. Existing cancellation semantics only; no new cancellation API."
  },
  "fallback_provenance": {
    "failed_issue": 988,
    "task_id": "task-1790145138643-8b6279b29e2f",
    "activation_head": "6e9f156a543293f37abc19a2dba6bc7b7364a852",
    "observed_failure": "401 Unauthorized: lease_invalid after approximately126seconds; default lease120seconds vs executor300seconds; zero tracked product delta. Child Windows tool environment missing necessary variables; literal percent-SystemDrive artifact observed, writer not conclusively established. Exact-session Windows shell evidence includes Cannot run document with missing PATHEXT; do not infer all cache-writer causation.",
    "preservation": "Preserve failed task/session/worktree and Issue988 Decision unchanged. Do not retry that task or reuse its authority. This document authorizes nothing until approved and activated."
  },
  "concurrent_work_preservation": {
    "981": "849af4ae2039bb7d30ebb442404a567e5c7152f2",
    "979": "73128ceac2d3efcab53e8e2964033da53143af2b",
    "978": "d4a227e63347972f3f3bfd3cea27fa7abb0f3222",
    "987": "2d5c2b1a5dd54320a1bfb3866eb2c513ad53a7c9",
    "policy": "Preserve all named remote heads and local Issue988 activation/failed child. No cherry-pick, import, closure, cleanup or mutation. Never edit task_service.py or tests/platform_v1/test_task_service.py owned by PR979. Preserve accepted983 OAuth proxy behavior and existing assistant evidence behavior.",
    "988_local": "6e9f156a543293f37abc19a2dba6bc7b7364a852"
  },
  "reference_paths": [
    "AGENTS.md",
    "docs/agents/governance-reference.md",
    "reverse_agent/platform_v1/task_execution.py",
    "reverse_agent/platform_v1/durable_execution.py",
    "reverse_agent/platform_v1/opencode_server_transport.py",
    "tests/platform_v1/test_opencode_server_transport.py",
    "tests/platform_v1/test_credential_relay.py",
    "tests/platform_v1/test_trusted_host.py",
    "tests/platform_v1/test_trusted_host_lifecycle.py"
  ],
  "runtime_scratch_policy": {
    "paths": [
      "**/__pycache__/**",
      ".pytest_cache/**"
    ],
    "stage_allowed": false,
    "note": "Only disposable test fixtures and external evidence/probes under F:/Nerelan-final-audit-evidence-20260911/issue989-probes; never touch live .platform_v1_runtime, user settings, failed task worktree or caches. No cleanup of previous artifacts."
  },
  "required_provider_free_checks": [
    "python -m pytest tests/platform_v1/test_execution_runtime_budget.py -q",
    "python -m pytest tests/platform_v1/test_opencode_executor.py tests/platform_v1/test_opencode_server_transport.py -q",
    "python -m pytest tests/platform_v1/test_credential_relay.py tests/platform_v1/test_trusted_host.py tests/platform_v1/test_trusted_host_lifecycle.py -q",
    "git diff --check"
  ],
  "allowed_commands": [
    {
      "command_id": "issue989v1.bootstrap",
      "command": "After fresh current main/base/ownership observation, create F:/Nerelan-issue989-execution-runtime-budget on codex/execution-runtime-budget-r3-v1-20260923 from exact 58d4068f43ca4914b122445685cae410a8fa156e. Commit only approved Decision once, then sequential startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre and worktree-publication-readiness. Require PRE_EXECUTION_AUTHORIZED and PUBLICATION_READY. No product edits before approval/activation/preflight; never alter activated Decision or commit generated gates.",
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
      "command_id": "issue989v1.implement",
      "command": "Supervisor implements only the five approved product paths and exact semantic contract after the observed system failure. Use synthetic fake-clock fixtures, bounded deadline-to-lease plumbing for CLI/server and minimal non-secret Windows child env. Preserve OAuth/proxy, assistant evidence, credential confinement and task execution semantics. New tests go in test_execution_runtime_budget.py; existing opencode executor tests may adapt only to legitimate budget/env contract changes, never weaken assertions. Other test/source files are read-only. No runtime, credentials, provider, model, OAuth, browser, install or network operations.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "source_edit",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/platform_v1/opencode_executor.py",
        "reverse_agent/platform_v1/trusted_host.py",
        "reverse_agent/model_access/credential_relay.py",
        "tests/platform_v1/test_opencode_executor.py",
        "tests/platform_v1/test_execution_runtime_budget.py"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "issue989v1.probes",
      "command": "At most six explicit installed Git/cmd.exe/Windows PowerShell provider-free probe subprocesses, each <=15seconds, use structured argv and isolated F:/Nerelan-final-audit-evidence-20260911/issue989-probes. Probe read-only Git version/repository observation and shell digest calculation against supervisor-created harmless fixture under the actual constrained candidate child env. No profile loading, shell-string user input, provider/credential access, network, browser, installs or runtime restart. Record command/env variable NAMES only, exit/output/digest and directory artifact names; never print env values or tokens. Demonstrate no literal percent-SystemDrive/SystemRoot cache artifacts from probes; preserve scratch and do not generalize observed writer identity. These six OS probes are distinct from ordinary subprocesses inside deterministic tests.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "integration_test",
        "local_static_check",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue989v1.validate",
      "command": "At most eight development check rounds before one frozen product commit using: python -m pytest tests/platform_v1/test_execution_runtime_budget.py -q; python -m pytest tests/platform_v1/test_opencode_executor.py tests/platform_v1/test_opencode_server_transport.py -q; python -m pytest tests/platform_v1/test_credential_relay.py tests/platform_v1/test_trusted_host.py tests/platform_v1/test_trusted_host_lifecycle.py -q; git diff --check. Tests use only fake/synthetic/local loopback data; no installed OpenCode/Codex model command. After development passes, commit the exact five-path product delta once and run each listed mandatory command once on that exact head, plus git diff --check 58d4068f43ca4914b122445685cae410a8fa156e HEAD and sequential startup-snapshot/transition-command-plan/transition-lint/transition-preflight/worktree-publication-readiness. Mandatory failure stops dependent publication; no fix-forward, rerun or extra product commit in this round.",
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
        "machine_specific_execution",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/platform_v1/opencode_executor.py",
        "reverse_agent/platform_v1/trusted_host.py",
        "reverse_agent/model_access/credential_relay.py",
        "tests/platform_v1/test_opencode_executor.py",
        "tests/platform_v1/test_execution_runtime_budget.py"
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
      "command_id": "issue989v1.publish",
      "command": "Only after exact mandatory tests/readiness and independent exact-head implementation audit, fresh locked main/ownership checks: publish identical local Decision plus product blob/tree/commit graph through canonical GitHub Git API to codex/execution-runtime-budget-r3-v1-20260923, verify every SHA, and create one exact-head Draft against main. Complete base-to-head delta limited to Decision and five approved product files; no generated gates. No local git push, remote semantic edits, mark-ready/merge, issue closure, refs except the one exact approved branch, dispatch/rerun, history rewrite or external publication.",
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
      "command_id": "issue989v1.natural_checks",
      "command": "Require unchanged applicable exact-head natural CI, Decision Preflight, State Gate and Model Access workflows; actual full CI exit0/native JUnit zero failures/errors. Verify precise triggers and run head/event/attempt. No workflow changes, reruns or dispatch, no custom CI bypass. Existing CI-only dependency setup stays unchanged; no local install.",
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
      "command_id": "issue989v1.audit",
      "command": "Read canonical main/base/head, Issue989, immutable Decision and actual natural artifacts; independently review exact source diff and deterministic fake-clock/Windows probe evidence. Verify frozen concurrent heads and preserve all older failed evidence. Keep Draft; do not claim deployment, system implementation success, live model/OAuth, UI repair or overall completion.",
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
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
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
      "Require unchanged applicable exact-head natural CI, Decision Preflight, State Gate and Model Access workflows; actual full CI exit0/native JUnit zero failures/errors. Verify precise triggers and run head/event/attempt. No workflow changes, reruns or dispatch, no custom CI bypass. Existing CI-only dependency setup stays unchanged; no local install."
    ],
    "trusted_worker_network_exceptions": [],
    "user_local_network_exceptions": [
      "At most eight development check rounds before one frozen product commit using: python -m pytest tests/platform_v1/test_execution_runtime_budget.py -q; python -m pytest tests/platform_v1/test_opencode_executor.py tests/platform_v1/test_opencode_server_transport.py -q; python -m pytest tests/platform_v1/test_credential_relay.py tests/platform_v1/test_trusted_host.py tests/platform_v1/test_trusted_host_lifecycle.py -q; git diff --check. Tests use only fake/synthetic/local loopback data; no installed OpenCode/Codex model command. After development passes, commit the exact five-path product delta once and run each listed mandatory command once on that exact head, plus git diff --check 58d4068f43ca4914b122445685cae410a8fa156e HEAD and sequential startup-snapshot/transition-command-plan/transition-lint/transition-preflight/worktree-publication-readiness. Mandatory failure stops dependent publication; no fix-forward, rerun or extra product commit in this round."
    ],
    "github_control_plane_network_exceptions": [
      "Only after exact mandatory tests/readiness and independent exact-head implementation audit, fresh locked main/ownership checks: publish identical local Decision plus product blob/tree/commit graph through canonical GitHub Git API to codex/execution-runtime-budget-r3-v1-20260923, verify every SHA, and create one exact-head Draft against main. Complete base-to-head delta limited to Decision and five approved product files; no generated gates. No local git push, remote semantic edits, mark-ready/merge, issue closure, refs except the one exact approved branch, dispatch/rerun, history rewrite or external publication."
    ]
  },
  "provider_free_network_boundaries": "user_local validate network exception permits test-owned loopback only; all non-loopback provider/model access forbidden. Canonical GitHub read-only observations use remote_observation. Publication limited to exact approved Draft graph. No runtime endpoints or user configuration mutations."
}
```
