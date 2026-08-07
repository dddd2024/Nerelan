# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260806_pr119_final_merge_authority_v4",
  "round_id": "round_20260806_pr119_final_merge_authority_v4",
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
  "follows_last_decision_id": "decision_20260806_pr119_active_intent_lifecycle_v3",
  "follows_last_round_id": "round_20260806_pr119_active_intent_lifecycle_v3",
  "previous_audit_outcome": "V3_REJECTED_DECISION_IMMUTABILITY_VIOLATION_AND_NO_MERGE_AUTHORITY",
  "workstream_id": "pr119-final-merge-authority-v4",
  "source_issue": 122,
  "active_pr": 119,
  "required_branch": "agent/frontend-v1-openhands-ui",
  "starting_head": "a8522cb2466bf157c1255cfdcb79c9dd157d34f2",
  "activation_base_sha": "1142dd324fdd4c4bf2a1353d9d5e93bc04b33507",
  "allowed_merge_method": "merge",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": false,
  "pr_body_update_allowed": false,
  "pr_comment_allowed": true,
  "issue_comment_allowed": false,
  "merge_allowed": true,
  "mark_ready_allowed": true,
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
      "command_id": "archive.pr119_v1_active_intent",
      "command": "byte-for-byte copy active.json to archive/pr119_v1.json",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["file_copy"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [
        "project_state/mainline_merge_intents/archive/pr119_v1.json"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "write.new_active_intent_v4",
      "command": "write new active.json bound to PR119 final merge authority v4",
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
      "command_id": "test.merge_intent_contracts",
      "command": "python -m pytest tests/platform_v1/test_merge_intent.py tests/platform_v1/test_contracts.py -q",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [
        "tests/platform_v1/test_merge_intent.py",
        "tests/platform_v1/test_contracts.py"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "test.platform_v1_full",
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
      "command_id": "validation.frontend_no_change",
      "command": "git diff --exit-code 68445abdcd6e66c3ad5c4534a9dd5c1c2414e47d HEAD -- frontend",
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
    },
    {
      "command_id": "observation.pr119",
      "command": "gh pr view 119 --repo dddd2024/reverse-agent --json number,state,isDraft,headRefName,headRefOid,baseRefName,baseRefOid,autoMergeRequest,mergeable,mergeStateStatus,url",
      "phase": "observation",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "observation.exact_head_workflows",
      "command": "gh pr checks 119 --repo dddd2024/reverse-agent",
      "phase": "observation",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "publication.owner_attestation_pr_comment",
      "command": "gh pr comment 119 --repo dddd2024/reverse-agent --body-file -",
      "phase": "publication",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["pr_comment", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "merge.mark_ready_pr119",
      "command": "gh pr ready 119 --repo dddd2024/reverse-agent",
      "phase": "merge",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["mark_ready", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "merge.merge_pr119_expected_head",
      "command": "gh pr merge 119 --repo dddd2024/reverse-agent --merge --match-head-commit <EXPECTED_HEAD>",
      "phase": "merge",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["merge", "network_access"],
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
    "project_state/mainline_merge_intents/archive/pr119_v1.json",
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
    "project_state/mainline_merge_intents/archive/pr67_v*.json",
    "project_state/mainline_merge_intents/archive/pr93_v*.json",
    "project_state/mainline_merge_intents/archive/pr97_v*.json",
    "project_state/mainline_merge_intents/archive/pr108_v*.json",
    "project_state/mainline_merge_intents/archive/pr110_v*.json",
    "project_state/mainline_merge_intents/archive/pr112_v*.json"
  ],
  "forbidden_operations": [
    "direct push to main",
    "force push",
    "rebase",
    "squash",
    "auto merge",
    "tag or release",
    "deployment",
    "credential access or publication",
    "real provider access",
    "PR #121 mutation",
    "modify frontend/**",
    "modify reverse_agent/**",
    "PR body modification",
    "delete historical or negative assertions",
    "weaken digest or workflow validation"
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
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [
      "git push origin agent/frontend-v1-openhands-ui",
      "gh pr view 119 --repo dddd2024/reverse-agent",
      "gh pr checks 119 --repo dddd2024/reverse-agent",
      "gh pr comment 119 --repo dddd2024/reverse-agent",
      "gh pr ready 119 --repo dddd2024/reverse-agent",
      "gh pr merge 119 --repo dddd2024/reverse-agent"
    ],
    "ci_network_exceptions": []
  },
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/**",
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr119_v1.json"
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

Bind the v4 Decision governance on the PR #119 branch `agent/frontend-v1-openhands-ui` to authorize final merge authority. Archive the current v3 active intent as `pr119_v1.json` byte-for-byte, bind a new v4 active intent to PR #119 with final merge authority under v4 Decision control, update both intent contract tests with immutability regression coverage, and verify all gates and tests pass. Merge (`merge` method only, with expected-head protection) and mark-ready are authorized after all four exact-head workflows and the remote Owner attestation are satisfied. The `frontend/**` tree must remain byte-for-byte identical relative to the anchored frontend baseline.

## Acceptance boundary

The v4 Decision is committed before any active intent, archive, or test changes. The transition Gate sequence must produce `transition-lint == PASSED`, `transition-preflight gate_status == PRE_EXECUTION_AUTHORIZED`, `blocking_reasons == []`. Active intent tests must continue to use `reverse_agent.project_state.extract_markdown_json_block` to parse `decision_meta` and `decision_contract`. New immutability regression tests verify: only one Decision commit in `starting_head..HEAD`, the current Decision file bytes equal the bytes at that Decision commit, the Decision commit precedes all implementation commits, and duplicate or illegal Decision JSON blocks must fail. PR #119 merge, mark-ready, attestation PR comment, PR #121 mutation, and direct main push remain outside this round's scope until separately authorized.
