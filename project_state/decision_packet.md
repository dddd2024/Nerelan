```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260724_stage_a_freeze_baseline_ci_repair_v1",
  "round_id": "round_20260724_stage_a_freeze_baseline_ci_repair_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
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
  "follows_last_decision_id": "decision_20260721_architecture_spine_trusted_execution_cutover_rework_v1",
  "follows_last_round_id": "round_20260721_architecture_spine_trusted_execution_cutover_rework_v1",
  "previous_audit_outcome": "ACCEPTED",
  "workstream_id": "stage-a-freeze-baseline-ci-repair-v1",
  "source_issue": 18,
  "source_pull_request": 9,
  "program_bundle_sha256": "394f02387230710cb158782affc77a11a651819a6e66221fae9ed95912295c97",
  "required_branch": "codex/stage-a-freeze-baseline-v1",
  "activation_base_sha": "38de9106d191d6b66d5f878354144817095e7bca",
  "frozen_previous_main_sha": "5884cf2abb37945652ef166cf0e78fa24593b0d5",
  "frozen_subject_head_sha": "43418818af61d9be3208d2444fd6ce5120f73fab",
  "frozen_merge_commit_sha": "38de9106d191d6b66d5f878354144817095e7bca",
  "frozen_pr11_head_sha": "d500c145a3201f59f90fcb330fc400596fba10b8",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json"
  ],
  "bootstrap_exception_commands": [],
  "allowed_commands": [
    {
      "command_id": "status.git_status",
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
      "command_id": "gate.command_plan",
      "command": "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["command_plan_generation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
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
      "operations": ["authority_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "gate.pre_execution",
      "command": "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["pre_execution_authorization"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [
        "project_state/gates/transition_preflight_result.json",
        "project_state/gates/bootstrap_state.json"
      ],
      "produced_artifacts": [
        "project_state/gates/transition_preflight_result.json",
        "project_state/gates/bootstrap_state.json"
      ]
    },
    {
      "command_id": "test.integration_baseline",
      "command": "python -m pytest tests/test_integration_baseline.py -q",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["integration_test"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "gate.integration_baseline",
      "command": "python -m reverse_agent.project_gate integration-baseline --state-dir project_state",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["baseline_validation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
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
      "command": "git push origin codex/stage-a-freeze-baseline-v1",
      "phase": "publication",
      "required": false,
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
    ".github/workflows/state-gate.yml",
    "docs/architecture/main-integration-baseline.md",
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/integration_baselines/architecture_spine_v1.json",
    "project_state/schemas/integration_baseline.schema.json",
    "reverse_agent/project_gate.py",
    "tests/test_integration_baseline.py"
  ],
  "reference_paths": [
    "project_state/current_state.json",
    "project_state/artifact_index.json",
    "project_state/state_manifest.json"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "project_state/gates/bootstrap_state.json"
  ],
  "forbidden_mutated_paths": [
    "frontend/**",
    "solve_reports/**",
    "local_reverse_samples/**",
    "training_materials/**",
    "reverse_agent/user_solve_*.py",
    "reverse_agent/strategies/**",
    "project_state/current_state.json",
    "project_state/artifact_index.json",
    "project_state/state_manifest.json",
    "project_state/context/**",
    "project_state/rounds/**",
    "project_state/audits/**",
    ".codex-skills/**",
    ".env",
    "**/secrets/**",
    "**/credentials/**",
    "**/*.exe",
    "**/*.dll",
    "**/*.bin"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "force_push",
    "rebase",
    "destructive",
    "unknown_binary_execution",
    "model_api_invocation",
    "external_reverse_tool_invocation",
    "runner_dispatch",
    "bmad_installation"
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
    "local_network_exceptions": [
      "git push origin codex/stage-a-freeze-baseline-v1"
    ],
    "ci_network_exceptions": [],
    "remote_observation_read_only_allowed": true
  },
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": [
    ".github/workflows/state-gate.yml",
    "project_state/decision_packet.md",
    "project_state/gates/**",
    "project_state/integration_baselines/**",
    "project_state/schemas/**",
    "reverse_agent/project_gate.py",
    "tests/test_integration_baseline.py",
    "docs/architecture/main-integration-baseline.md"
  ],
  "path_risk_floor": [
    {"pattern": ".github/workflows/**", "minimum_risk": "R2"},
    {"pattern": "project_state/decision_packet.md", "minimum_risk": "R2"},
    {"pattern": "project_state/gates/**", "minimum_risk": "R2"},
    {"pattern": ".env", "minimum_risk": "R3"},
    {"pattern": "**/secrets/**", "minimum_risk": "R3"},
    {"pattern": "**/credentials/**", "minimum_risk": "R3"},
    {"pattern": "**/*.exe", "minimum_risk": "R3"},
    {"pattern": "**/*.dll", "minimum_risk": "R3"},
    {"pattern": "**/*.bin", "minimum_risk": "R3"}
  ],
  "scope_policy": "stage_a_freeze_baseline_ci_repair_only",
  "stop_after_exact_head_ci": true
}
```

# DECISION_PACKET

## Goal

Close Stage A after the exact-head merge of PR #9 by replacing branch-only
main validation with a fail-closed frozen integration-baseline check.

The frozen Architecture Spine baseline is:

- previous main: `5884cf2abb37945652ef166cf0e78fa24593b0d5`;
- accepted PR #9 head: `43418818af61d9be3208d2444fd6ce5120f73fab`;
- merge commit: `38de9106d191d6b66d5f878354144817095e7bca`;
- merge tree: exactly equal to the accepted PR #9 head tree;
- PR #11 remains read-only at `d500c145a3201f59f90fcb330fc400596fba10b8`.

## Required implementation

1. Add a versioned, schema-validated integration baseline receipt.
2. Add a fail-closed CLI gate that verifies the receipt, commit objects,
   two-parent merge ancestry, parent ordering, and tree equality.
3. Keep transition lint/plan/preflight on pull-request and non-main branches.
4. Run the integration-baseline gate on pushes to `main`.
5. Add focused tests and architecture documentation.

## Do not do

Do not modify PR #9 or PR #11 branches, solve artifacts, samples, frontend,
reverse-solving logic, dependencies, secrets, binaries, tags, or releases.
Do not execute unknown binaries. Do not push directly to main, force-push,
rebase, or merge under this Decision.

## Completion

This Decision is complete only when local focused tests pass, the branch is
published in a new PR, and exact-head CI, State Gate, and Decision Preflight
are green. The PR then waits for a separately authorized merge.
