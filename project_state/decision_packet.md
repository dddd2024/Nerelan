# Approved bounded provider-free execution diagnostic

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260923_local_execution_probe_r3_v1",
  "round_id": "round_20260923_local_execution_probe_r3_v1",
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
  "decision_scope": "SUPERVISED_PROVIDER_FREE_LOCAL_EXECUTION_DIAGNOSTIC",
  "source_issue": 448,
  "parent_issue": 260,
  "approved_by": "dddd2024 via explicit delegated Owner completion",
  "approval_basis": "User explicitly delegated Owner completion while retaining supervisor testing/task assignment and Nerelan-only product implementation. Independent candidate boundary review accepted SHA256 d3be07f10ee891b751e96c57cbd4e04de28dfd7828c21786845b876e865a83a4. This distinct finite provider-free diagnostic authorizes only the listed synthetic probes and external report, zero real models/product changes/services/credentials/publication. Exact harness and activation review remain required.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R3",
  "integration_base_ref": "codex/ux14-timeout-evidence-r3-v1-20260923",
  "base_sha": "a438c404d5d858846d9faf3c8ccaca8a53a7cf45",
  "activation_base_sha": "a438c404d5d858846d9faf3c8ccaca8a53a7cf45",
  "starting_head": "a438c404d5d858846d9faf3c8ccaca8a53a7cf45",
  "fresh_base": "a438c404d5d858846d9faf3c8ccaca8a53a7cf45",
  "current_main_expected": "58d4068f43ca4914b122445685cae410a8fa156e",
  "required_branch": "codex/local-execution-probe-r3-v1-20260923",
  "workstream_id": "local-execution-probe-r3-v1",
  "follows_last_decision_id": "decision_20260923_ux14_timeout_evidence_r3_v1",
  "follows_last_round_id": "round_20260923_ux14_timeout_evidence_r3_v1",
  "workflow_profile": "browser_r3",
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 0,
  "generated_governance_commit_limit": 0,
  "normal_push_attempt_limit": 0,
  "draft_pr_creation_limit": 0,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "workflow_dispatch_limit": 0,
  "credential_access_limit": 0,
  "local_browser_launch_limit": 0,
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
  "live_provider_access_allowed": false,
  "credential_access_allowed": false,
  "unknown_binary_execution_allowed": false,
  "model_api_invocation_allowed": false,
  "external_reverse_tool_invocation_allowed": false,
  "destructive_operations_allowed": false,
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
    "project_state/gates/transition_preflight_result.json"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
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
    "**/.env",
    "reverse_agent/**",
    "tests/**",
    "frontend/**"
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
    "system_task_dispatch",
    "runtime_service_restart",
    "runtime_synchronization",
    "product_source_edit"
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
    "specification": "Testing only. External thin synthetic HTTP/SSE upstream and isolated fixture harness under nerelan-audit/local-execution-probe-v1. Known installed OpenCode binary hash pinned. No product changes or real model calls. Reuse existing credential relay and configuration helpers only with in-memory fake credentials. Capture bounded partial stdout/stderr, request metadata, complete synthetic tool replies and actual fixture file hashes. Verify program-level isolation by independent static harness/config review before binary execution. No OS sandbox enforcement claim, and no production timeout root-cause claim from synthetic success/failure alone.",
    "completion_boundary": "At most one version command and four sequential synthetic probes, first failure stops remaining probes. Independent evidence review and concrete diagnostic task/report. No product acceptance, runtime update or publication."
  },
  "runtime_scratch_policy": {
    "paths": [
      "**/__pycache__/**",
      ".pytest_cache/**"
    ],
    "stage_allowed": false,
    "note": "All new harness, fixture repositories, isolated configuration/home/temp/data and output files exclusively under existing external nerelan-audit/local-execution-probe-v1. Never copy/read user config, credentials, caches or histories. Preserve probe artifacts and all existing worktrees."
  },
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
    "ci_network_exceptions": [],
    "trusted_worker_network_exceptions": [],
    "user_local_network_exceptions": [
      "Freshly verify accepted local base a438c404d5d858846d9faf3c8ccaca8a53a7cf45 and original workspace HEAD/status; read-only bounded main/PR991 context. Independently review candidate and approval-only transformation under existing explicit Owner delegation. Create only F:/Nerelan-local-execution-probe-20260923 on codex/local-execution-probe-r3-v1-20260923 from exact local base; commit approved Decision only once. Generate actual startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre and worktree-publication-readiness; require PRE_EXECUTION_AUTHORIZED/PUBLICATION_READY and independent exact activation acceptance before probe execution.",
      "Execute at most one known OpenCode --version command with10-second limit and then at most four sequential60-second probes in probe_budget order under probe_isolation. Direct fake answer, then existing in-memory credential relay fake answer, then marker read and edit. First failed mandatory stage ends this round without retry or fixes. Zero real model calls; random127.0.0.1 local fake endpoints only. Capture bounded stdout/stderr even on timeout, exact request/event/actual file evidence; terminate only owned probe processes and close local fake servers. Preserve all artifacts.",
      "Run git diff --check on Decision-only host; verify unchanged original/source/runtime and all product paths. Independently inspect actual probe evidence, distinguish harness/fixture limitations from production root cause. Update external audit report and submit concrete diagnostic/fix task via existing localhost8766 Inbox only if new actionable evidence; preserve existing tickets and never execute another system/model Task under this Decision."
    ],
    "github_control_plane_network_exceptions": []
  },
  "allowed_commands": [
    {
      "command_id": "probev1.bootstrap",
      "command": "Freshly verify accepted local base a438c404d5d858846d9faf3c8ccaca8a53a7cf45 and original workspace HEAD/status; read-only bounded main/PR991 context. Independently review candidate and approval-only transformation under existing explicit Owner delegation. Create only F:/Nerelan-local-execution-probe-20260923 on codex/local-execution-probe-r3-v1-20260923 from exact local base; commit approved Decision only once. Generate actual startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre and worktree-publication-readiness; require PRE_EXECUTION_AUTHORIZED/PUBLICATION_READY and independent exact activation acceptance before probe execution.",
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
      "command_id": "probev1.harness",
      "command": "Write only external testing harness and synthetic fixtures in nerelan-audit/local-execution-probe-v1. Static review existing installed binary/program-level configuration and adapter paths. Independently accept exact harness bytes and config isolation before execution. Python compile-only syntax check permitted; no import-executing installed CLI or real credentials. No product edits.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "local_static_check",
        "machine_specific_execution",
        "source_edit"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "probev1.probe",
      "command": "Execute at most one known OpenCode --version command with10-second limit and then at most four sequential60-second probes in probe_budget order under probe_isolation. Direct fake answer, then existing in-memory credential relay fake answer, then marker read and edit. First failed mandatory stage ends this round without retry or fixes. Zero real model calls; random127.0.0.1 local fake endpoints only. Capture bounded stdout/stderr even on timeout, exact request/event/actual file evidence; terminate only owned probe processes and close local fake servers. Preserve all artifacts.",
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
        "unit_test",
        "integration_test"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "probev1.report",
      "command": "Run git diff --check on Decision-only host; verify unchanged original/source/runtime and all product paths. Independently inspect actual probe evidence, distinguish harness/fixture limitations from production root cause. Update external audit report and submit concrete diagnostic/fix task via existing localhost8766 Inbox only if new actionable evidence; preserve existing tickets and never execute another system/model Task under this Decision.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "diff_validation",
        "local_static_check",
        "machine_specific_execution",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "reference_paths": [
    "AGENTS.md",
    "docs/agents/governance-reference.md",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/model_access/credential_relay.py",
    "tests/platform_v1/test_task3c_v5_opencode_probe.py"
  ],
  "system_task_attempt_limit": 0,
  "gpt_model_invocation_limit": 0,
  "model_budget_semantics": "Zero real model/provider calls; zero system Task creation/dispatch; no production runtime, settings, services or database mutations except at most one new Inbox candidate with diagnostic evidence through the explicitly named existing localhost8766 Inbox API. No existing record/state changes, promotion or execution.",
  "source_inbox_id": "inbox-1790158620782-05e360330915",
  "concurrent_work_preservation": {
    "main": "58d4068f43ca4914b122445685cae410a8fa156e",
    "991": "f015eed511e3b1226e7ef1f2db22dd5b26fe47f5",
    "989_source_head": "ad18e253183fdf0d4e10f3f6e2c2054af0e22332",
    "988_source_head": "6e9f156a543293f37abc19a2dba6bc7b7364a852",
    "policy": "Read-only preserve all existing worktrees, failed children, services and data. Fresh exact local base and original workspace identities required. Remote main/PR991 observation is context only. No runtime synchronization, service action or publication.",
    "ux05_host_head": "de2305bc29b18c90bbb293cbdda22a8d8bc0565f",
    "ux05_child": "F:/Nerelan-first-use-task-workspaces-20260923/task-1790157323936-ed09d6308845"
  },
  "accepted_base_evidence": {
    "head": "a438c404d5d858846d9faf3c8ccaca8a53a7cf45",
    "review_path": "C:\\Users\\wjc27\\.codex\\visualizations\\2026\\09\\23\\01a0cd45-5b28-7132-8f0e-7daa29cd0350\\nerelan-audit\\ux14-activation-independent-review.json",
    "review_sha256": "6744a80d78f6a2ffcb1f5fec19ecd468c510f020bfb95c00f6c8c18dc776c231",
    "scope": "Accepted immutable activation-only base, not UX14 product acceptance."
  },
  "probe_budget": {
    "version_commands": 1,
    "version_timeout_seconds": 10,
    "probe_limit": 4,
    "probe_timeout_seconds": 60,
    "sequential_order": [
      "direct_fake_answer",
      "relay_fake_answer",
      "relay_fake_read_marker",
      "relay_fake_edit_marker"
    ],
    "stop_on_first_failure": true,
    "max_requests_per_probe": 8,
    "max_request_bytes": 1048576,
    "max_output_bytes_per_stream": 1048576,
    "known_executable": "C:/Users/wjc27/AppData/Roaming/npm/node_modules/opencode-ai/bin/opencode.exe",
    "known_executable_sha256": "fd254474def7ee35f07416cf4674c361f07e7bcd9c7ffb284af21bb011066ee3",
    "known_executable_bytes": 178673032
  },
  "probe_isolation": "Each attempt uses a new synthetic Git fixture and isolated HOME, USERPROFILE, APPDATA, LOCALAPPDATA, XDG_CONFIG_HOME/XDG_CACHE_HOME/XDG_DATA_HOME/XDG_STATE_HOME, OPENCODE_TEST_HOME, TEMP/TMP. Build minimal environment from explicit OS/process requirements; no inherited provider keys, proxies, node options, plugins or user config. Set existing supported flags to disable auto updates, model fetch, LSP downloads, default/external plugins/skills, project and external Claude configuration; --pure; synthetic inline config has no MCP, LSP, external instructions, remote refs or plugins. Only bundled @ai-sdk/openai-compatible at a random loopback127.0.0.1 ephemeral fake HTTP upstream/relay; no redirects/fallback/real credential store. Independently verify actual permission semantics, deny shell/subagent/network/outside file tools and only permit named synthetic marker/prompt file access. Git global/system configs disabled. Installed known executable and Python/Git dependencies already present only, no installation/download. Bound each process in a Windows kill-on-close Job Object if available using standard ctypes before starting its thread, preserving exact owned PID/start/path; fail before execution if process ownership confinement unavailable. On timeout terminate only the owned probe process group, never shared services. Never claim OS network/filesystem sandboxing. Also isolate OPENCODE_TEST_MANAGED_CONFIG_DIR and use OPENCODE_AUTH_CONTENT={} to bypass real auth reads. Isolate npm user/global configs and cache, offline=true with loopback registry only. To prevent the statically confirmed background Npm.install path, create explicitly synthetic no-install sentinels (empty node_modules plus package-lock root dependency key @opencode-ai/plugin) in each isolated configuration directory. These are test branch controls, not installed plugins or production setup; record exact metadata hashes, forbid claiming a dependency installed. --pure keeps external plugin loading disabled. No npm command or actual install is authorized. Independent exact harness review must confirm this branch control before CLI launch."
}
```
