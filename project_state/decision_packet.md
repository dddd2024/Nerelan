# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260806_pr119_active_intent_lifecycle_v3",
  "round_id": "round_20260806_pr119_active_intent_lifecycle_v3",
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
  "follows_last_decision_id": "decision_20260806_pr119_active_intent_lifecycle_v2",
  "follows_last_round_id": "round_20260806_pr119_active_intent_lifecycle_v2",
  "previous_audit_outcome": "PR119_ACTIVE_INTENT_LIFECYCLE_V2_COMPLETE",
  "workstream_id": "pr119-active-intent-lifecycle-v3",
  "source_issue": 122,
  "active_pr": 119,
  "required_branch": "agent/frontend-v1-openhands-ui",
  "starting_head": "68445abdcd6e66c3ad5c4534a9dd5c1c2414e47d",
  "activation_base_sha": "1142dd324fdd4c4bf2a1353d9d5e93bc04b33507",
  "allowed_merge_method": "merge",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": false,
  "pr_body_update_allowed": false,
  "pr_comment_allowed": false,
  "issue_comment_allowed": false,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_allowed": false,
  "release_allowed": false,
  "deployment_allowed": false,
  "real_provider_credential_allowed": false,
  "live_work_item_publication_allowed": false,
  "trusted_host_live_probe_allowed": false,
  "repair_attempt_limit": 1,
  "audit_generation_allowed": false,
  "prior_audits_immutable": true,
  "bootstrap_state_initial": "ACTIVE",
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "observation.git_status",
      "command": "git status --short",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "gate.startup_snapshot",
      "command": "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "bootstrap_exception",
      "bootstrap_exception": true,
      "allowed_mutated_paths": [
        "project_state/gates/startup_snapshot.json"
      ],
      "produced_artifacts": [
        "project_state/gates/startup_snapshot.json"
      ]
    },
    {
      "command_id": "gate.transition_command_plan",
      "command": "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "bootstrap_exception",
      "bootstrap_exception": true,
      "allowed_mutated_paths": [
        "project_state/gates/command_plan.json",
        "project_state/gates/transition_command_plan_preview.json"
      ],
      "produced_artifacts": [
        "project_state/gates/command_plan.json",
        "project_state/gates/transition_command_plan_preview.json"
      ]
    },
    {
      "command_id": "gate.transition_lint",
      "command": "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "bootstrap_exception",
      "bootstrap_exception": true,
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "gate.transition_preflight",
      "command": "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "bootstrap_exception",
      "bootstrap_exception": true,
      "allowed_mutated_paths": [
        "project_state/gates/transition_preflight_result.json",
        "project_state/gates/bootstrap_state.json"
      ],
      "produced_artifacts": [
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "archive.pr112_v6",
      "command": "byte-for-byte copy active.json to archive/pr112_v6.json",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["file_copy"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [
        "project_state/mainline_merge_intents/archive/pr112_v6.json"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "write.new_active_intent",
      "command": "write new active.json for PR119",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["write_file"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [
        "project_state/mainline_merge_intents/active.json"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "test.pytest_merge_intent",
      "command": "python -m pytest tests/platform_v1/test_merge_intent.py -q",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "test.pytest_contracts",
      "command": "python -m pytest tests/platform_v1/test_contracts.py -q",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "test.pytest_platform_v1",
      "command": "python -m pytest tests/platform_v1 -q",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "test.pytest_mainline",
      "command": "python -m pytest tests/test_mainline_landing.py tests/test_integration_baseline.py tests/test_project_audits.py -q",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "test.pytest_gate_transition",
      "command": "python -m pytest tests/test_project_gate.py tests/test_control_plane_transition.py tests/test_decision_preflight.py tests/test_project_state.py -q",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "validation.diff_check",
      "command": "git diff --check",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["diff_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "publication.push_branch",
      "command": "git push origin agent/frontend-v1-openhands-ui",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["push", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr112_v6.json",
    "tests/platform_v1/test_merge_intent.py",
    "tests/platform_v1/test_contracts.py"
  ],
  "reference_paths": [
    "AGENTS.md",
    "README.md",
    ".github/workflows/ci.yml",
    ".github/workflows/decision-preflight.yml",
    ".github/workflows/state-gate.yml",
    "reverse_agent/project_gate.py",
    "reverse_agent/project_state.py",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/platform_v1/authority_adapter.py",
    "tests/test_mainline_landing.py",
    "tests/test_integration_baseline.py",
    "tests/test_project_audits.py",
    "tests/test_project_gate.py",
    "tests/test_control_plane_transition.py",
    "tests/test_decision_preflight.py",
    "tests/test_project_state.py"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "project_state/gates/bootstrap_state.json"
  ],
  "forbidden_mutated_paths": [
    "frontend/**",
    "reverse_agent/**",
    "docs/**",
    "deploy/**",
    "examples/**",
    "pyproject.toml",
    "requirements*.txt",
    "poetry.lock",
    "uv.lock",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/schemas/**",
    "project_state/rounds/**",
    "project_state/audits/**",
    "project_state/mainline_merge_intents/archive/pr97_v*.json",
    "project_state/mainline_merge_intents/archive/pr108_v*.json",
    "project_state/mainline_merge_intents/archive/pr110_v*.json",
    "project_state/mainline_merge_intents/archive/pr67_v*.json",
    "project_state/mainline_merge_intents/archive/pr93_v*.json",
    "project_state/mainline_merge_intents/archive/pr97_v*.json"
  ],
  "forbidden_operations": [
    "direct push to main",
    "force push",
    "rebase",
    "squash",
    "merge",
    "mark ready",
    "auto merge",
    "tag or release",
    "deployment",
    "credential access or publication",
    "real provider access",
    "PR #121 mutation",
    "accepted frontend branch mutation",
    "modify frontend/**",
    "modify reverse_agent/**",
    "delete historical or negative assertions",
    "weaken digest or workflow validation",
    "fall back to an older successful workflow run"
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
    "local_network_exceptions": [
      "git push origin agent/frontend-v1-openhands-ui"
    ],
    "ci_network_exceptions": []
  },
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/**",
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr112_v6.json"
  ],
  "path_risk_floor": [
    {
      "pattern": ".github/workflows/**",
      "minimum_risk": "R2"
    },
    {
      "pattern": "project_state/decision_packet.md",
      "minimum_risk": "R2"
    },
    {
      "pattern": "project_state/gates/**",
      "minimum_risk": "R2"
    },
    {
      "pattern": "project_state/mainline_merge_intents/**",
      "minimum_risk": "R2"
    }
  ]
}
```

## Goal

Embed the v3 Decision governance directly on the PR #119 branch `agent/frontend-v1-openhands-ui`. Archive the current PR #112 v6 active intent as `pr112_v6.json` byte-for-byte, bind a new active intent to PR #119 with the v3 Decision authority, update active intent assertions in tests to use the canonical Markdown JSON-block parser (not regex), add archive presence and identity checks for `pr112_v6.json`, and verify all gates and tests pass. Publication is limited to a non-force push to `agent/frontend-v1-openhands-ui`. The `frontend/**` tree must remain byte-for-byte identical relative to starting HEAD `68445abd`.

## Acceptance boundary

The v3 Decision is committed before any active intent or test changes. The transition Gate sequence must produce `transition-lint == PASSED`, `transition-preflight gate_status == PRE_EXECUTION_AUTHORIZED`, `blocking_reasons == []`. Active intent tests must use `reverse_agent.project_state.extract_markdown_json_block` to parse `decision_meta` and `decision_contract`, not regex. The parser must reject duplicate or malformed JSON blocks. All historical archive tests must remain unchanged; only new `pr112_v6.json` checks are added. After pushing, no further action is taken in this round. PR #119 merge, mark-ready, PR #121 mutation, and direct main push remain forbidden.
