# Windows owned fixture lifecycle repair

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20261001_issue1047_windows_owned_shutdown_r3_v1",
  "round_id": "round_20261001_issue1047_windows_owned_shutdown_r3_v1",
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
  "decision_scope": "WINDOWS_OWNED_FIXTURE_LIFECYCLE_REPAIR",
  "source_issue": 1047,
  "parent_issue": 289,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 via explicit user approval 2026-10-01T04:02:30Z Sentinel_738c3b494528819196b021a484258575",
  "approval_basis": "User approved the assistant proposal: isolated reproduction, edits to dev-up/dev-down and corresponding tests, stop ONLY identity-verified test-created processes; no other processes. User confirmed continuing responsibility at 2026-10-01T04:02:53Z Sentinel_06d2a4e71b988191a4f73f5274609416. This is a fresh bounded Decision, not reuse of #1042 or #1044. Issue comments are tracking, not authority.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "9092911f41a089e249f27c883526904299be1d17",
  "activation_base_sha": "9092911f41a089e249f27c883526904299be1d17",
  "starting_head": "9092911f41a089e249f27c883526904299be1d17",
  "required_branch": "owner/20261001-windows-owned-shutdown-r3-v1",
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
  "product_change_commit_limit": 5,
  "generated_governance_commit_limit": 0,
  "normal_push_attempt_limit": 7,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "workflow_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
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
  "live_provider_access_allowed": false,
  "credential_access_allowed": false,
  "local_browser_execution_allowed": false,
  "model_api_invocation_allowed": false,
  "external_reverse_tool_invocation_allowed": false,
  "unknown_binary_execution_allowed": false,
  "destructive_operations_allowed": true,
  "provider_free_acceptance_required": true,
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "semantic_implementation_contract": {
    "specification": "Reproduce the four historical Windows launcher failures using actual current main scripts and fixture functions. Capture taskkill returncode/stdout/stderr and exact PID, executable and start-time before stop; never stop live/user/unknown/reused processes. Establish actual cause before repair. Fix only the necessary dev-up/dev-down lifecycle and corresponding tests; preserve strict identity refusal, unknown-port refusal and launcher semantics. Record process exit, owned LISTEN disappearance and restart readiness separately. Socket timeout/unreachable is not evidence of port free. Windows PowerShell 5.1 and PowerShell 7 must exercise actual script behavior. #1004 timestamp coercion is distinct until demonstrated; no unrelated framework replacement.",
    "reuse": "Existing scripts, Process identity APIs, native taskkill and provider-free Windows fixture. No copied verifier, no governance/check changes, no dependencies.",
    "execution_surface_note": "Fresh full isolated checkout on hostname dd under authorized Temp. Bootstrap Decision-only activation precedes generated plan, lint and actual PRE_EXECUTION_AUTHORIZED. After preflight, at most 16 focused scenario/probe executions, 2 Platform suite runs and 2 repository suite runs, within 4 hours. Known existing Python, PowerShell, cmd and taskkill only. Loopback fixture listeners only. Destructive permission means solely termination of newly created fixture processes whose exact PID/executable/start-time and fixture ownership have been verified immediately before stop, and documented descendants created by that fixture. No files deleted or moved; no unknown or user processes terminated. Evidence may be written only within this isolated Temp work/evidence area and external pytest basetemp under authorized Temp. Record failures and preserve evidence.",
    "completion_boundary": "One Draft, three product paths, immutable Decision bootstrap only; generated artifacts not committed. Author tests are not independent acceptance. Natural exact-head CI, no reruns/dispatch. Update #1047/#1010/#289/#1004/#1041 with factual progress; fresh-read and surgically update stale #1010 current status, preserve history/concurrent modifications. No source issue closure, Ready, merge, deploy, settings, credentials or payment."
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
    "dev-up.ps1",
    "dev-down.ps1",
    "tests/platform_v1/test_dev_up_contract.py"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "dev-up.ps1",
    "dev-down.ps1",
    "tests/platform_v1/test_dev_up_contract.py"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "AGENTS.md",
    "docs/agents/governance-reference.md",
    ".codex-skills/reverse-agent-iteration/SKILL.md",
    "tests/test_mainline_landing.py",
    ".github/workflows/ci.yml"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md",
    "docs/agents/**",
    ".github/**",
    ".codex-skills/**",
    "reverse_agent/control_plane/**",
    "reverse_agent/model_access/**",
    "reverse_agent/project_gate.py",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/platform_v1/**",
    "tests/test_mainline_landing.py",
    "frontend/**",
    "project_state/rounds/**",
    "project_state/mainline_merge_intents/**",
    "launch_nerelan.bat",
    "launch_reverse_agent.bat",
    "pyproject.toml",
    "requirements*.txt",
    "**/secrets/**",
    "**/.env",
    "reverse_agent/github_remote_verifier.py",
    "tests/platform_v1/test_check_producer_binding.py",
    "docs/check-producer-binding.md"
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
    "model_api_invocation",
    "provider_network_call",
    "credential_access",
    "unknown_binary_execution",
    "external_reverse_tool_invocation",
    "tag_or_release",
    "dependency_install",
    "local_browser_execution",
    "generated_governance_commit"
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
    "ci_network_exceptions": [
      "Unchanged natural CI dependency setup and provider-free tests only. No rerun or dispatch."
    ],
    "trusted_worker_network_exceptions": [
      "Within isolated dd Temp checkout, run the four exact retained Windows launcher tests/scenarios and narrow lifecycle probes using existing installed PS5/PS7/Python, actual scripts and fixture helpers. Capture exact identity, taskkill returncode/stdout/stderr, process exit, owned LISTEN and readiness. Stop only freshly created identity-verified fixture processes/descendants; never unknown/live/user processes. Bounded loopback only; preserve evidence and do not erase fixtures.",
      "Run focused Windows launcher regressions on actual PS5 and PS7, tests/test_mainline_landing.py, applicable Platform V1 and repository deterministic pytest, git diff --check, within declared budgets. Test fixture process cleanup uses the same exact ownership constraint; no model/provider calls, installs or unknown binary."
    ],
    "user_local_network_exceptions": [],
    "github_control_plane_network_exceptions": [
      "Publish only owner/20261001-windows-owned-shutdown-r3-v1 and one Draft against main@9092911f41a089e249f27c883526904299be1d17. Update exact head binding and factual tracking #1047/#1010/#289/#1004/#1041, preserving concurrent/history content. No Ready/merge/closure/settings/deployment."
    ]
  },
  "path_risk_floor": [
    {
      "pattern": "project_state/**",
      "minimum_risk": "R2"
    },
    {
      "pattern": "dev-up.ps1",
      "minimum_risk": "R3"
    },
    {
      "pattern": "dev-down.ps1",
      "minimum_risk": "R3"
    }
  ],
  "allowed_commands": [
    {
      "command_id": "windows.bootstrap",
      "command": "Run existing startup-snapshot, transition-command-plan, transition-lint and transition-preflight --mode pre; require PRE_EXECUTION_AUTHORIZED before fixture execution or implementation. Worktree-publication-readiness before scoped staging/publication. Preserve gates uncommitted.",
      "phase": "bootstrap",
      "required": false,
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
      "command_id": "windows.reproduce",
      "command": "Within isolated dd Temp checkout, run the four exact retained Windows launcher tests/scenarios and narrow lifecycle probes using existing installed PS5/PS7/Python, actual scripts and fixture helpers. Capture exact identity, taskkill returncode/stdout/stderr, process exit, owned LISTEN and readiness. Stop only freshly created identity-verified fixture processes/descendants; never unknown/live/user processes. Bounded loopback only; preserve evidence and do not erase fixtures.",
      "phase": "diagnosis",
      "required": false,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "trusted_worker",
      "operations": [
        "unit_test",
        "local_static_check",
        "destructive",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "windows.implement",
      "command": "After actual preflight and causal reproduction, minimally repair dev-up.ps1/dev-down.ps1 and corresponding actual-function tests only. Preserve identity and unknown-port fail-closed semantics. Do not alter judges, governance, workflows, dependencies or other candidates.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "trusted_worker",
      "operations": [
        "source_edit",
        "local_static_check"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "dev-up.ps1",
        "dev-down.ps1",
        "tests/platform_v1/test_dev_up_contract.py"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "windows.validate",
      "command": "Run focused Windows launcher regressions on actual PS5 and PS7, tests/test_mainline_landing.py, applicable Platform V1 and repository deterministic pytest, git diff --check, within declared budgets. Test fixture process cleanup uses the same exact ownership constraint; no model/provider calls, installs or unknown binary.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "trusted_worker",
      "operations": [
        "unit_test",
        "local_static_check",
        "diff_validation",
        "destructive",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "windows.publish",
      "command": "Publish only owner/20261001-windows-owned-shutdown-r3-v1 and one Draft against main@9092911f41a089e249f27c883526904299be1d17. Update exact head binding and factual tracking #1047/#1010/#289/#1004/#1041, preserving concurrent/history content. No Ready/merge/closure/settings/deployment.",
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
      "command_id": "windows.observe",
      "command": "Read exact remote head/base, scoped diff, immutable Decision and natural CI until terminal. Disclose actual local vs CI results and remaining independent acceptance.",
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
    }
  ],
  "issue_completion_close_allowed": []
}
```
